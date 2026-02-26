import os
import random
from datetime import time, datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==============================
# CONFIGURAÇÕES
# ==============================
TOKEN = "8760211159:AAGjucI7T5HfdUKAPgVOMw74imsPRFHfrxU"           # 🔴 Seu token do BotFather
CHAT_ID = -1003754183745               # 🔴 Seu chat/grupo ID
CAMINHO_ARQUIVO = "questoes/constitucional.txt"
ARQUIVO_PROGRESSO = "progresso.txt"
QUESTOES_POR_DIA = 15

# ==============================
# LEITURA DAS QUESTÕES
# ==============================
def carregar_questoes():
    with open(CAMINHO_ARQUIVO, "r", encoding="utf-8") as f:
        conteudo = f.read()
    questoes = [q.strip() for q in conteudo.split("===") if q.strip()]
    return questoes

def limitar_explicacao(texto):
    # Telegram limita explicações longas; corta se necessário
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

# ==============================
# CONTROLE DE PROGRESSO
# ==============================
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
# COMANDOS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Bot de Questões ATIVO!\n"
        "Envio diário sequencial habilitado.\n"
        "Comentários aparecem apenas após responder."
    )

# comando manual (aleatório)
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

# ==============================
# ENVIO AUTOMÁTICO SEQUENCIAL
# ==============================
async def enviar_automatico(context: ContextTypes.DEFAULT_TYPE):
    questoes = carregar_questoes()
    inicio = ler_progresso()
    fim = inicio + QUESTOES_POR_DIA
    bloco = questoes[inicio:fim]

    if not bloco:  # reinicia ao final
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
# INICIALIZAÇÃO E WEBHOOK
# ==============================
PORT = int(os.environ.get("PORT", 5000))
URL_RENDER = "https://bot1-pmpe.onrender.com/"  # 🔴 Sua URL do Render

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("questao", questao))

# agendar envio diário usando JobQueue
from telegram.ext import JobQueue
job_queue = app.job_queue
job_queue.run_daily(enviar_automatico, time=time(hour=12, minute=0))

print("Bot rodando (modo produção)...")

# roda webhook
app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=URL_RENDER
)