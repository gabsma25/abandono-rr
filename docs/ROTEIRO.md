# Roteiro: as metas M1–M12 do projeto anterior

**Origem:** `abandono-escolar/docs/DECISOES.md`, commit `878930f`, linhas 1577–1622 (entrada "2026-11-10 —
Roteiro: metas futuras de implementação (não iniciadas)"). A seção abaixo é uma **cópia literal**, sem nenhuma
alteração; os números que ela traz são do arquivo e não foram regerados aqui. O texto foi escrito para a
pergunta antiga (prever o abandono do ano seguinte), antes da mudança de escopo de 2026-11-14
(`docs/DECISOES.md`).

## Estado de cada meta no escopo novo

Nenhuma meta foi iniciada, e nenhuma foi decidida para o escopo novo. Cada uma será revista pelo grupo, e o que
for decidido vai para o `docs/DECISOES.md` e, se virar avaliação, para o `docs/PROTOCOLO.md`, antes de rodar.

| Meta | No escopo novo |
|---|---|
| M1 D8 na base | a revisar |
| M2 Teto de previsibilidade | a revisar |
| M3 Histórico encolhido | a revisar |
| M4 Lista selada para 2026 | a revisar |
| M5 Etapa 3 com TDI | a revisar |
| M6 Censo ampliado | a revisar |
| M7 Transferência | a revisar |
| M8 Equidade e calibração | a revisar |
| M9 Modelo misto / duas partes | a revisar |
| M10 Ajuste fino | a revisar |
| M11 IED 2019–2020, HAD e Pé-de-Meia | a revisar |
| M12 Integração dos repositórios | a revisar |

## Cópia literal do arquivo

> ## 2026-11-10 — Roteiro: metas futuras de implementação (não iniciadas)
>
> *Plano da pesquisadora, depois do resultado da classificação na janela
> 2013–2018. Nenhuma meta está iniciada. Cada uma terá protocolo próprio
> registrado aqui antes de rodar. A ordem e o escopo serão confirmados com o
> orientador.*
>
> Diagnóstico que orienta o roteiro: a ferramenta empata com a régua porque (1)
> o sinal é fraco (abandono(t) × abandono(t−1): Pearson 0,25 no AF, 0,23 no EM;
> síntese §3.5) e escolas pequenas têm taxa ruidosa; (2) a janela segura só tem
> rendimento, território e infraestrutura, sem o TDI, a única variável com sinal
> próprio na Etapa 2; (3) há poucas escolas por ano. A prioridade é mais
> informação e menos ruído, não algoritmos mais complexos.
>
> Regras para todas as metas:
>
> - toda escolha de desenho (variável, janela de anos, hiperparâmetro, limiar) é
>   feita só com os anos de treino, por validação interna;
> - uma melhoria só é afirmada se confirmada em dados que não serviram para
>   desenhá-la: o teste prospectivo de 2026 (previsões seladas), outros estados
>   como validação externa, ou a Etapa 3, se desenhada antes de ver resultados;
> - os anos de teste 2016–2019 (classificação) e 2021–2024 (Etapa 2) não são
>   usados de novo para escolher nada;
> - o resultado é reportado como sair, inclusive nulo, com a leitura GANHO / SEM
>   GANHO PRÁTICO / INCONCLUSIVO.
>
> | Meta | O que é | Critério de conclusão | Depende de |
> |---|---|---|---|
> | M1 D8 na base | Escola indígena, localização diferenciada, matrícula da etapa (QT_MAT), multisseriada e elegivel_analise, do Censo 2019–2025 já no disco | Colunas na base com teste; contagens por ano | decisão de 10/11 |
> | M2 Teto de previsibilidade | Quanto do "alto risco" seria esperado só por sorte, dado o tamanho de cada escola; Recall@20% máximo esperado por simulação | Tabela por etapa e ano; descritivo | M1 (2019–2025); download para 2013–2018 |
> | M3 Histórico encolhido | Média do abandono dos últimos 2 a 3 anos, puxada para a média da rede conforme o tamanho da escola; como variável e como régua nova (B3) | Desenho fixado só nos anos de treino; comparação "modelo × melhor regra simples" | M1 |
> | M4 Lista selada para 2026 | Previsões com t = 2025, faixas alto/moderado/baixo e principais sinais; sha256 de código, base e lista registrados; inclui a hipótese do EM (bloco 2, +0,06) | Arquivo e hashes no DECISOES antes de o INEP publicar o desfecho de 2026 | — |
> | M5 Etapa 3 com TDI | Downloads de 2011–2019 (TDI, ATU, tx_rend, Censo) no MANIFEST; replicação na janela segura com TDI (PROPOSTA de 10/11) | Protocolo registrado; execução única | downloads (autorizados em 10/11); zips do Gustavo |
> | M6 Censo ampliado | Porte, docentes, turmas, tempo integral, turno noturno (README da v1.0, §13) | Variáveis na base com regra de fonte e teste | M5 |
> | M7 Transferência | Treinar com escolas do Brasil (indicadores 2019–2025 já no disco, que cobrem todo o país) e aplicar em Roraima; validação externa em outro estado | Protocolo próprio; comparação com o modelo só de Roraima | M1; alinhado ao desenho do edital |
> | M8 Equidade e calibração | Desempenho e calibração por grupo (indígena, rural, interior, capital) | Tabela por grupo com IC | M1 |
> | M9 Modelo misto / duas partes | Efeito de escola (encolhimento formal) e modelo zero × positivo, da proposta do orientador | Protocolo próprio | M3 |
> | M10 Ajuste fino | Hiperparâmetros só por validação interna nos anos de treino | Registro das escolhas antes do teste | — |
> | M11 IED 2019–2020, HAD e Pé-de-Meia | Conferência de compatibilidade metodológica; marcação pós-2024; sensibilidade com e sem 2024–2025 | Registro da conferência; família de testes declarada | decisão de 10/11 |
> | M12 Integração dos repositórios | Unificar os trabalhos dos três integrantes | Um repositório com histórico e documentação únicos | grupo |
>
> Ordem proposta: M1 → M2 → M3 → M4 → M5/M6 → M7 → M8 → M9/M10; M11 e M12 em
> paralelo. M2 vem cedo porque diz quanto ainda dá para ganhar: se o teto
> estiver perto da régua, a conclusão do artigo é que dados anuais por escola
> não permitem antecipar muito melhor que a persistência, e o projeto passa a
> priorizar M7 e dados de frequência.
