import socketio

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = socketio.ASGIApp(sio, static_files={
    "/": "client/index.html",
    "/assets": "client/assets",      # mapa, tileset e sprites da vila
})

# A partir da Etapa 1, adicione o seu código ABAIXO desta linha.
CUSTO = 40              # ervas por laboratório
TEMPO_OBRA = 10         # segundos até o laboratório ficar pronto
INTERVALO = 4           # segundos entre as colheitas
GANHO_OBRA = 4          # ervas a mais por colheita a cada laboratório pronto
ERVAS_POR_POCAO = 5     # cada laboratório troca 5 ervas por 1 poção por intervalo
CUSTO_INSTAVEL = 20     # ervas para preparar uma poção instável
PRAZO_INSTAVEL = 15     # segundos para estabilizar antes de expirar
GANHO_INSTAVEL = 3      # poções ganhas ao estabilizar


estado = {
    "fase": "aguardando",     # aguardando -> aberta -> encerrada
    "ervas": 120,
    "pocoes": 0,
    "trabalhadores": 0,       # alquimistas ocupados agora
    "limite": 3,              # máximo de alquimistas
    "producao": 8,            # ervas colhidas a cada INTERVALO
    "intervalo": INTERVALO,
    "tempo_obra": TEMPO_OBRA,
    "custo": CUSTO,
    "concluidas": 0,          # laboratórios prontos
    "em_obra": 0,
    "instavel": False,        # existe uma poção instável agora?
    "custo_instavel": CUSTO_INSTAVEL,
    "prazo_instavel": PRAZO_INSTAVEL,
}

jogadores = {}                # sid -> {"nome": ..., "papel": ...}
numero_instavel = 0           # identifica a poção instável atual (para o prazo)

def fato(causa, **extras):
    """Monta o payload de um FATO: o estado atual, a CAUSA (o evento ou o
    temporizador que gerou o fato) e dados extras."""
    return {"estado": dict(estado), "causa": causa, **extras}

@sio.event
async def connect(sid, environ, auth):
    auth = auth or {}
    jogadores[sid] = {
        "nome": auth.get("nome", "Anônimo"),
        "papel": auth.get("papel", "jogador"),
    }
    # servidor -> UM cliente (to=sid): só quem acabou de entrar precisa do estado
    # atual; os outros já o têm e nada mudou para eles
    await sio.emit("estado.sincronizado", fato("conexao"), to=sid)

@sio.event
async def disconnect(sid):
    jogadores.pop(sid, None)

async def recusar(sid, motivo, causa):
    """Responde só a quem pediu (to=sid): a recusa não muda o estado,
    então os outros jogadores não têm o que atualizar."""
    await sio.emit("operacao.recusada", {"motivo": motivo, "causa": causa}, to=sid)

@sio.on("vila.abertura_solicitada")
async def abrir_vila(sid, dados=None):
    pedido = "vila.abertura_solicitada"
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode abrir a temporada", pedido)
        return
    if estado["fase"] != "aguardando":
        await recusar(sid, "A temporada já foi aberta", pedido)
        return
    estado["fase"] = "aberta"
    sio.start_background_task(colheita)
    # FATO para todos: a temporada mudou para todo mundo, não só para o Mestre
    await sio.emit("vila.iniciada", fato(pedido))


@sio.on("laboratorio.construcao_solicitada")
async def construir(sid, dados=None):
    pedido = "laboratorio.construcao_solicitada"
    # Valide TUDO antes de alterar o estado e sem await no meio:
    # assim, dois pedidos simultâneos são decididos um de cada vez.
    if estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif estado["ervas"] < CUSTO:
        motivo = "Ervas insuficientes"
    elif estado["trabalhadores"] >= estado["limite"]:
        motivo = "Sem alquimista livre"
    else:
        motivo = None

    if motivo:
        await recusar(sid, motivo, pedido)    # só quem pediu recebe
        return

    estado["ervas"] -= CUSTO
    estado["trabalhadores"] += 1
    estado["em_obra"] += 1
    nome = jogadores[sid]["nome"]
    # FATO para todos: as ervas e os alquimistas são da vila inteira,
    # então todas as telas precisam mostrar a obra e o novo saldo
    await sio.emit("laboratorio.iniciado", fato(pedido, por=nome))
    # o temporizador da obra vai gerar laboratorio.concluido depois
    sio.start_background_task(obra, nome)


async def colheita():
    while estado["fase"] == "aberta":
        await sio.sleep(INTERVALO)
        if estado["fase"] != "aberta":
            break
        estado["ervas"] += estado["producao"]
        # recurso refinado: cada laboratório pronto troca ervas por 1 poção
        for _ in range(estado["concluidas"]):
            if estado["ervas"] < ERVAS_POR_POCAO:
                break
            estado["ervas"] -= ERVAS_POR_POCAO
            estado["pocoes"] += 1
        # FATO sem pedido: a causa é o tempo passando, e todos veem a colheita
        await sio.emit("ervas.colhidas", fato("temporizador"))


async def obra(nome):
    await sio.sleep(TEMPO_OBRA)
    if estado["fase"] != "aberta":
        return
    estado["trabalhadores"] -= 1
    estado["em_obra"] -= 1
    estado["concluidas"] += 1
    estado["producao"] += GANHO_OBRA
    causa = "laboratorio.iniciado (temporizador)"
    # FATO para todos: o laboratório pronto libera um alquimista e aumenta a
    # colheita da vila inteira
    await sio.emit("laboratorio.concluido", fato(causa, por=nome))


# ----- Evento próprio: poção instável com prazo -----
@sio.on("pocao_instavel.preparo_solicitado")
async def preparar_instavel(sid, dados=None):
    global numero_instavel
    pedido = "pocao_instavel.preparo_solicitado"
    if estado["fase"] != "aberta":
        motivo = "A temporada não está aberta"
    elif estado["instavel"]:
        motivo = "Já existe uma poção instável"
    elif estado["ervas"] < CUSTO_INSTAVEL:
        motivo = "Ervas insuficientes"
    else:
        motivo = None

    if motivo:
        await recusar(sid, motivo, pedido)
        return

    estado["ervas"] -= CUSTO_INSTAVEL
    estado["instavel"] = True
    numero_instavel += 1
    nome = jogadores[sid]["nome"]
    # FATO para todos: qualquer alquimista pode estabilizar, então todos
    # precisam saber que existe uma poção instável e qual é o prazo
    await sio.emit("pocao_instavel.preparada", fato(pedido, por=nome))
    # o temporizador do prazo pode gerar pocao_instavel.expirada depois
    sio.start_background_task(prazo_instavel, numero_instavel)


@sio.on("pocao_instavel.estabilizacao_solicitada")
async def estabilizar(sid, dados=None):
    pedido = "pocao_instavel.estabilizacao_solicitada"
    if estado["fase"] != "aberta":
        await recusar(sid, "A temporada não está aberta", pedido)
        return
    if not estado["instavel"]:
        await recusar(sid, "Não há poção instável para estabilizar", pedido)
        return
    estado["instavel"] = False
    estado["pocoes"] += GANHO_INSTAVEL
    nome = jogadores[sid]["nome"]
    # FATO para todos: o alerta some em todas as telas e as poções aumentam
    await sio.emit("pocao_instavel.estabilizada", fato(pedido, por=nome))


async def prazo_instavel(numero):
    await sio.sleep(PRAZO_INSTAVEL)
    # só expira se ainda for a mesma poção e ninguém a estabilizou
    if estado["fase"] != "aberta" or not estado["instavel"] or numero != numero_instavel:
        return
    estado["instavel"] = False
    causa = "pocao_instavel.preparada (temporizador)"
    # FATO sem pedido: ninguém causou a expiração, foi o prazo que acabou;
    # todos precisam tirar o alerta da tela
    await sio.emit("pocao_instavel.expirada", fato(causa))


@sio.on("vila.encerramento_solicitado")
async def encerrar_vila(sid, dados=None):
    pedido = "vila.encerramento_solicitado"
    if jogadores[sid]["papel"] != "mestre":
        await recusar(sid, "Só o Mestre pode encerrar a temporada", pedido)
        return
    if estado["fase"] != "aberta":
        await recusar(sid, "A temporada não está aberta", pedido)
        return
    estado["fase"] = "encerrada"
    # FATO para todos: a temporada acabou para todos; colheita, obras e
    # prazos param porque conferem a fase antes de agir
    await sio.emit("vila.encerrada", fato(pedido))
