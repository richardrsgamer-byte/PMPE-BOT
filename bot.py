import os
import random
import asyncio
from datetime import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("8760211159:AAGjucI7T5HfdUKAPgVOMw74imsPRFHfrxU")  # 🔴 Use variável de ambiente no Render
CHAT_ID = int(os.environ.get("CHAT_ID", "-1003754183745"))  # 🔴 também variável de ambiente
CAMINHO_ARQUIVO = "questoes/constitucional.txt"
ARQUIVO_PROGRESSO = "progresso.txt"
QUESTOES_POR_DIA = 15

# ==============================
# FUNÇÕES
# ==============================
def carregar_questoes():
    with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
        conteudo = f.read()
    return [q.strip() for q in conteudo.split("===") if q.strip()]

def limitar_explicacao(texto):
    if len(texto) > 200:
        return texto[:197] + "..."
    return texto

def parsear_questao(texto):
    linhas = texto.split("\n")
    pergunta = ""
    opcoes = []
    correta = ""
    comentario = ""
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith("PERGUNTA:"):
            pergunta = linha.replace("PERGUNTA:", "").strip()
        elif linha.startswith(("A)", "B)", "C)", "D)", "E)")):
            opcoes.append(linha[3:].strip())
        elif linha.startswith("CORRETA:"):
            correta = linha.replace("CORRETA:", "").strip()
        elif linha.startswith("COMENTARIO:"):
            comentario = linha.replace("COMENTARIO:", "").strip()
    comentario = limitar_explicacao(comentario)
    indice_correto = ["A", "B", "C", "D", "E"].index(correta)
    return pergunta, opcoes, indice_correto, comentario

def ler_progresso():
    try:
        with open(ARQUIVO_PROGRESSO, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def salvar_progresso(valor):
    with open(ARQUIVO_PROGRESSO, "w") as f:
        f.write(str(valor))

# ==============================
# HANDLERS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Bot de Questões ATIVO!\n"
        "Envio diário sequencial habilitado.\n"
        "Comentários aparecem apenas após responder."
    )

async def questao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    questoes = carregar_questoes()
    q = random.choice(questoes)
    pergunta, opcoes, correta, comentario = parsear_questao(q)
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=pergunta,
        options=opcoes,
        type="quiz",
        correct_option_id=correta,
        explanation=comentario,
        is_anonymous=True
    )

async def enviar_automatico(context: ContextTypes.DEFAULT_TYPE):
    questoes = carregar_questoes()
    inicio = ler_progresso()
    fim = inicio + QUESTOES_POR_DIA
    bloco = questoes[inicio:fim]
    if not bloco:
        inicio = 0
        fim = QUESTOES_POR_DIA
        bloco = questoes[inicio:fim]
    for q in bloco:
        pergunta, opcoes, correta, comentario = parsear_questao(q)
        await context.bot.send_poll(
            chat_id=CHAT_ID,
            question=pergunta,
            options=opcoes,
            type="quiz",
            correct_option_id=correta,
            explanation=comentario,
            is_anonymous=True
        )
    salvar_progresso(fim)

# ==============================
# MAIN ASSÍNCRONO
# ==============================
async def main():
    PORT = int(os.environ.get("PORT", 5000))
    URL_RENDER = os.environ.get("RENDER_EXTERNAL_URL", "https://bot1-pmpe.onrender.com/")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("questao", questao))

    # JobQueue diário
    job_queue = app.job_queue
    job_queue.run_daily(enviar_automatico, time=time(hour=12, minute=0))

    print("Bot rodando (modo produção)...")

    # webhook
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{URL_RENDER}/bot"
    )

# ==============================
# EXECUTAR
# ==============================
if __name__ == "__main__":
    asyncio.run(main())