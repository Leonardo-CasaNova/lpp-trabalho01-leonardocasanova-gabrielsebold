# Especificação — Vila em Tempo Real

**Integrante(s):** (nome e @ do GitHub)
**Tipo de vila (sorteio):** (preencha)

> Escreva este documento ANTES do código e faça o commit antes da Etapa 0.
> Descreva o comportamento na linguagem da vila. Não cite tecnologia.

## 1. Regras da vila

- Recurso primário e recurso refinado: ...
- Custo de uma construção: ...
- Tempo da obra: ...
- Limite de trabalhadores: ...
- Intervalo e quantidade da produção automática: ...
- O que muda quando uma obra termina: ...

## 2. Eventos

| Evento | Emite | Recebe | O que muda no estado |
|---|---|---|---|
| `vila.iniciada` | Servidor | Todos | ... |
| `construcao.solicitada` | Jogador | Servidor | (é um pedido; nada muda) |
| `construcao.iniciada` | Servidor | Todos | ... |
| `operacao.recusada` | Servidor | Só quem pediu | ... |
| `recurso.produzido` | Servidor | Todos | ... |
| `construcao.concluida` | Servidor | Todos | ... |
| `vila.encerrada` | Servidor | Todos | ... |

(Renomeie os eventos para o seu tipo de vila e acrescente os que criar.)

## 3. Cenários de teste (Dado / Quando / Então, escritos com eventos)

### Recusa
Dado ..., quando ..., então ...

### Passagem do tempo
Dado ..., quando ..., então ...

### Disputa entre dois jogadores
Dado ..., quando os jogadores A e B emitem ... ao mesmo tempo, então ...
