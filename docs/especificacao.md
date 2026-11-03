# Especificação — Vila em Tempo Real

**Integrante(s):** Leonardo Casa Nova (@Leonardo-CasaNova) e Gabriel Sebold (@Gabriel-Sebold)
**Tipo de vila (sorteio):** Vila de Alquimia (ervas → poções)

> Escreva este documento ANTES do código e faça o commit antes da Etapa 0.
> Descreva o comportamento na linguagem da vila. Não cite tecnologia.

## 1. Regras da vila

- Recurso primário e recurso refinado: **ervas** 🌿 (colhidas na estufa) e **poções** 🧪 (preparadas nos laboratórios).
- A vila começa com 120 ervas, 0 poções e 0 laboratórios.
- Custo de uma construção: um **laboratório** custa 40 ervas.
- Tempo da obra: 10 segundos.
- Limite de trabalhadores: 3 **alquimistas**. Cada laboratório em obra ocupa um alquimista até ficar pronto.
- Intervalo e quantidade da produção automática: a cada 4 segundos a estufa colhe 8 ervas.
- No mesmo intervalo, cada laboratório pronto transforma 5 ervas em 1 poção (se houver ervas suficientes).
- O que muda quando uma obra termina: o alquimista fica livre, o laboratório passa a contar como pronto, a colheita aumenta em 4 ervas e a vila passa a produzir 1 poção a mais por intervalo.
- **Poção instável:** um alquimista pode preparar uma poção instável por 20 ervas. Ela precisa ser estabilizada em até 15 segundos. Estabilizada, vira 3 poções. Se o prazo acabar, ela expira e as ervas são perdidas. Só existe uma poção instável por vez.
- Só o Mestre abre e encerra a temporada.

## 2. Eventos

| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `estado.sincronizado` | Servidor | Só quem entrou | Nada muda; o novo cliente recebe o estado atual |
| `vila.abertura_solicitada` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.iniciada` | Servidor | Todos | Fase passa de "aguardando" para "aberta"; a colheita começa |
| `laboratorio.construcao_solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `laboratorio.iniciado` | Servidor | Todos | Ervas −40; alquimistas ocupados +1; laboratórios em obra +1 |
| `operacao.recusada` | Servidor | Só quem pediu | Nada muda; o cliente vê o motivo |
| `ervas.colhidas` | Servidor (temporizador) | Todos | Ervas +colheita; cada laboratório pronto troca 5 ervas por 1 poção |
| `laboratorio.concluido` | Servidor (temporizador) | Todos | Alquimistas ocupados −1; em obra −1; prontos +1; colheita +4 |
| `pocao_instavel.preparo_solicitado` | Jogador | Servidor | (é um pedido; nada muda) |
| `pocao_instavel.preparada` | Servidor | Todos | Ervas −20; passa a existir uma poção instável com prazo de 15 s |
| `pocao_instavel.estabilizacao_solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `pocao_instavel.estabilizada` | Servidor | Todos | A poção instável deixa de existir; poções +3 |
| `pocao_instavel.expirada` | Servidor (temporizador) | Todos | A poção instável deixa de existir; nada é ganho |
| `vila.encerramento_solicitado` | Mestre | Servidor | (é um pedido; nada muda) |
| `vila.encerrada` | Servidor | Todos | Fase passa para "encerrada"; colheita, obras e prazos param |

Motivos de `operacao.recusada`: temporada não está aberta, ervas insuficientes, sem alquimista livre, já existe uma poção instável, não há poção instável para estabilizar, só o Mestre pode abrir/encerrar.

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado que a temporada está aberta e a vila tem 30 ervas, quando o jogador emite `laboratorio.construcao_solicitada`, então só ele recebe `operacao.recusada` com o motivo "Ervas insuficientes" e as ervas continuam 30.

### Passagem do tempo
Dado que a temporada está aberta, a colheita é 8 e há 1 laboratório pronto, quando passam 4 segundos, então todos recebem `ervas.colhidas` com ervas +8 −5 e poções +1.

Dado que um jogador recebeu `pocao_instavel.preparada`, quando passam 15 segundos sem `pocao_instavel.estabilizacao_solicitada`, então todos recebem `pocao_instavel.expirada` e as poções não mudam.

### Disputa entre dois jogadores
Dado que a temporada está aberta, há 1 alquimista livre e 120 ervas, quando os jogadores A e B emitem `laboratorio.construcao_solicitada` ao mesmo tempo, então o servidor atende um pedido por vez: todos recebem um único `laboratorio.iniciado` (ervas 80, alquimistas 3/3) e o outro jogador recebe `operacao.recusada` com "Sem alquimista livre".

Dado que existe uma poção instável, quando A e B emitem `pocao_instavel.estabilizacao_solicitada` ao mesmo tempo, então todos recebem um único `pocao_instavel.estabilizada` (poções +3) e o outro recebe `operacao.recusada` com "Não há poção instável para estabilizar".
