# Vila em Tempo Real — Vila de Alquimia (ervas → poções)

## Integrantes
- Leonardo Casa Nova — @Leonardo-CasaNova
- Gabriel Sebold — @Gabriel-Sebold

## Como instalar e executar
1. Tenha o Python 3.10 ou mais novo instalado.
2. Na pasta do projeto, crie e ative um ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Inicie o servidor:
   ```bash
   uvicorn server:app --reload
   ```
5. Abra http://localhost:8000 no navegador.

## Como testar com duas abas
1. **Aba 1:** digite um nome e clique em **Entrar como Mestre**.
2. **Aba 2:** digite outro nome e clique em **Entrar como Jogador** (abra uma terceira aba como Jogador para testar a disputa).
3. Na aba do Jogador, clique em **Construir laboratório** antes de abrir a temporada. Só essa aba recebe `operacao.recusada` ("A temporada não está aberta") e a tela treme.
4. Na aba do Mestre, clique em **Abrir temporada**. Todas as abas recebem `vila.iniciada` e a faixa muda para "Temporada de colheita aberta".
5. A cada 4 s, todas as abas recebem `ervas.colhidas` e mostram "+8 🌿".
6. No Jogador, clique em **Construir laboratório**. Todas as abas recebem `laboratorio.iniciado`: as ervas caem 40, um alquimista fica ocupado e aparece a obra no mapa. Depois de 10 s chega `laboratorio.concluido`: o laboratório aparece pronto, a colheita sobe 4 e cada colheita passa a gerar 1 poção.
7. Clique em Construir até faltar ervas ou alquimistas para ver a recusa com o motivo.
8. Clique em **Preparar poção instável**. Todas as abas recebem `pocao_instavel.preparada` e mostram o alerta. Clique em **Estabilizar poção** em menos de 15 s: todas recebem `pocao_instavel.estabilizada` e as poções sobem 3. Prepare outra e espere 15 s: todas recebem `pocao_instavel.expirada`.
9. Disputa: com duas abas de Jogador, clique em Estabilizar nas duas ao mesmo tempo. Só uma estabiliza; a outra recebe "Não há poção instável para estabilizar".
10. Na aba do Mestre, clique em **Encerrar temporada**. Todas recebem `vila.encerrada` e a vila escurece.

Em todas as abas, o **Painel de eventos** mostra cada evento com ⬆ emit ou ⬇ on, a causa, os dados e a reação, além dos contadores por evento.

## Perguntas
1. **Quais eventos o seu sistema emite e escuta?**
   - O cliente emite (pedidos): `vila.abertura_solicitada`, `vila.encerramento_solicitado` (Mestre), `laboratorio.construcao_solicitada`, `pocao_instavel.preparo_solicitado` e `pocao_instavel.estabilizacao_solicitada` (Jogador).
   - O servidor escuta esses pedidos e emite os fatos: `estado.sincronizado` e `operacao.recusada` (só para um cliente), e `vila.iniciada`, `laboratorio.iniciado`, `ervas.colhidas`, `laboratorio.concluido`, `pocao_instavel.preparada`, `pocao_instavel.estabilizada`, `pocao_instavel.expirada` e `vila.encerrada` (para todos).
   - O cliente escuta todos os fatos com `ouvir(...)`. A tabela completa, com o que muda no estado, está em `docs/especificacao.md`.
2. **Como o sistema sabe quando deve atualizar os outros jogadores?** O estado fica só no servidor. Sempre que ele muda (por um pedido aceito ou por um temporizador), o servidor emite um fato para todos com `sio.emit(...)` sem `to=`, e o fato leva o estado novo. Cada cliente, ao ouvir o fato, copia o estado e redesenha a tela. Quando nada muda (recusa) ou só um cliente precisa saber (entrada), o servidor usa `to=sid`.
3. **Que parte do código mostra claramente o uso do paradigma orientado a eventos?** No `server.py`, os handlers `@sio.on("laboratorio.construcao_solicitada")` e `@sio.on("pocao_instavel.estabilizacao_solicitada")` reagem a pedidos, e os temporizadores `colheita()`, `obra()` e `prazo_instavel()` geram fatos sem nenhum clique. No `client/index.html`, o bloco de `ouvir(...)` dentro de `entrar()` mostra que a tela só muda em reação a eventos, e as funções `pedir(...)` mostram que o cliente nunca altera o estado sozinho.

## Uso de IA
Usamos o assistente Kiro (IDE com IA) na Etapa 8 para adaptar a vila de exemplo ao tema de alquimia. Ele ajudou a preencher a especificação, renomear eventos e textos, criar o recurso refinado (poções) e o evento próprio (poção instável com prazo), editar o mapa e escrever comentários e este README. Revisamos o código, conferimos que os nomes batem entre especificação, servidor e cliente, e testamos com várias abas.

## Créditos da arte
Mapa, tileset e sprites são a arte original fornecida com o trabalho (uso livre na disciplina). O mapa `client/assets/vila.json` foi personalizado para a vila de alquimia: toras viraram canteiros de ervas, tocos viraram arbustos e o ponto `acampamento` virou `estufa`. Nenhuma arte de terceiros foi usada.

## Extras
- Recurso refinado (poções) **e** evento próprio (poção instável que expira).
