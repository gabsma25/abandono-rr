# Como contribuir

Somos três pessoas trabalhando no mesmo repositório, em máquinas diferentes. Este guia existe para que
ninguém quebre o trabalho de ninguém e para que todo número do projeto continue tendo uma origem verificável.

## Fluxo de trabalho do grupo

Este é o passo a passo de como os três trabalham juntos no `abandono-rr`. As regras gerais (padrão de commit,
versões, dados brutos fora do git, as regras do projeto) estão nas outras seções deste guia; aqui está a rotina.

**O `main` só recebe mudanças por pull request revisado por outra pessoa.** Ninguém faz commit nem push direto
no `main`, nem para corrigir uma vírgula.

### 1. Primeiro dia (uma vez por pessoa)

1. Clone o repositório e crie o ambiente:
   ```bash
   git clone https://github.com/gabsma25/abandono-rr.git
   cd abandono-rr
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # Linux/macOS
   pip install -r requirements.txt
   ```
2. Baixe os dados brutos **pelo módulo de aquisição**, que confere o hash de cada arquivo:
   `python -m src.aquisicao --baixar` (do INEP) ou `python -m src.aquisicao --origem-local PASTA` (de uma
   pasta). Ninguém copia dados por pendrive, WhatsApp ou e-mail: um arquivo sem hash conferido não entra no
   projeto.
3. Rode tudo uma vez:
   ```bash
   python rodar_tudo.py
   ```
   Se passar, a sua máquina reproduz exatamente o projeto. **Se falhar, esse é o primeiro problema a resolver**,
   antes de qualquer tarefa. Abra uma issue com a mensagem de erro.
4. Instale o limpador de notebooks (ver o item 3 desta seção):
   ```bash
   pip install nbstripout
   nbstripout --install
   ```

### 2. O ciclo de cada tarefa

```text
issue  →  branch  →  commits pequenos  →  rodar_tudo.py  →  pull request  →  revisão  →  merge  →  apagar o branch
```

1. **Issue.** Toda tarefa começa como uma issue no GitHub, com um responsável e uma frase dizendo o que fica
   pronto. A lista de issues é o registro de quem fez o quê, e serve de base para a autoria no TCC e no PIBIC.
2. **Atualize o `main` local e crie o branch:**
   ```bash
   git switch main
   git pull
   git switch -c tipo/descricao-curta    # ex.: feat/mlp-regressor, docs/protocolo, fix/funil-2015
   ```
   Tipos: `feat` (novidade), `fix` (correção), `docs` (documentação), `test` (testes), `chore` (manutenção).
   Uma tarefa = um branch. Não junte duas coisas sem relação no mesmo branch.
3. **Commits pequenos**, um assunto por commit, no padrão de mensagem do projeto (seção abaixo).
4. **Antes de abrir o pull request**, rode `python rodar_tudo.py`. Ele tem que passar inteiro. Se um teste
   aparecer como pulado (`skipped`), leia o motivo: quase sempre são os zips do INEP que faltam na sua máquina
   (`python -m src.aquisicao --origem-local PASTA`).
5. **Abra o pull request** pelo modelo em `.github/`, ligando a issue (`Fecha #12`). Diga o que mudou, por que
   mudou e como conferir.
6. **Outra pessoa revisa.** Ninguém aprova o próprio pull request. O revisor:
   - roda `python rodar_tudo.py` no branch;
   - confere que nenhum número foi digitado à mão (todo número vem de código);
   - confere que nada foi escolhido olhando o conjunto de teste;
   - comenta ou aprova.
7. **Quem abriu o pull request faz o merge**, depois da aprovação.
8. **Apague o branch**, no GitHub e na sua máquina (`git branch -d tipo/descricao-curta`).

### 3. Três armadilhas a evitar

**Notebooks em conflito.** Um `.ipynb` guarda o código, as saídas e as imagens no mesmo arquivo. Se duas pessoas
o editam ao mesmo tempo, o conflito no git é quase impossível de resolver. Por isso:
- **um notebook, um dono por vez**: quem vai mexer avisa na issue;
- as saídas são limpas antes do commit (o `nbstripout`, instalado no primeiro dia, faz isso sozinho);
- o notebook só exibe o que os scripts de `src/` gravaram; o cálculo fica no código, não no notebook.

**Pull requests grandes.** Um pull request com 40 arquivos não é revisado de verdade, só aprovado. Prefira vários
pequenos, um por assunto. Se a tarefa for grande, divida a issue.

**"Funciona na minha máquina".** É para isso que existem o `rodar_tudo.py` antes de cada pull request e o `.venv`
com versões fixadas. Não instale pacotes fora do `requirements.txt`; se precisar de um pacote novo, ele entra no
`requirements.txt` pelo mesmo pull request que o usa.

### 4. Ritmo do grupo

- **Uma conversa curta por semana** para olhar as issues abertas: o que fechou, o que travou, quem pega o quê.
- **Uma tag de versão a cada marco** (por exemplo, `v0.2.0` quando o novo protocolo rodar), com a entrada
  correspondente no `CHANGELOG.md`.
- **Decisões de método** (o que mudar no protocolo, qual variável entra) são registradas no `docs/DECISOES.md`
  **antes** de rodar, e passam por pull request como qualquer outra mudança.

### 5. Se você usa o Claude Code

O `CLAUDE.md` tem as regras do projeto, e o Claude Code as lê sozinho. Mesmo assim:
- peça que ele trabalhe num branch e pare antes de fazer merge ou push;
- revise o que ele fez como revisaria o trabalho de um colega: o pull request dele passa pela mesma revisão de
  outra pessoa do grupo.

## Mensagens de commit

O mesmo padrão do projeto anterior: **tipo, dois-pontos, descrição em português, verbo no presente da 3ª
pessoa, sem ponto final, até cerca de 72 caracteres.**

```
feat: Adiciona a matrícula da etapa ao dataset
fix: Corrige o limiar de alto risco quando há empate
test: Confere o funil de 2025 contra o projeto anterior
docs: Registra a decisão sobre o limiar de 20%
chore: Atualiza o MANIFEST com os zips de 2011
```

Tipos: `feat` (algo novo), `fix` (correção), `test` (testes), `docs` (documentação), `chore` (manutenção),
`refactor` (reorganiza sem mudar resultado). **Um commit por alteração coerente**: se a descrição precisa de
"e", provavelmente são dois commits.

## Dados no git

- **Nunca** ponha no git os dados brutos do INEP (zips, planilhas, CSVs de microdados). Eles são grandes e
  públicos; quem precisar obtém pelo script.
- No git ficam só: o `dados/MANIFEST.csv`, com o sha256 de cada arquivo; o recorte de Roraima em
  `dados/cache/`, que é pequeno e não tem outra fonte para 2007–2018; e o dataset versionado em `dataset/`.
- Para obter os zips: `python -m src.aquisicao --origem-local PASTA` (copia de uma pasta) ou
  `python -m src.aquisicao --baixar` (baixa do INEP). Os dois conferem o sha256 de cada arquivo contra o
  MANIFEST e recusam arquivo divergente.
- Se você precisar de um arquivo novo do INEP, isso é uma decisão do grupo: abra um pull request que
  acrescenta a linha no MANIFEST e registra o motivo no `docs/DECISOES.md`.

## Experimentos

Para testar uma ideia sem mexer no núcleo, crie uma pasta em `experimentos/<nome>/` (veja
[`experimentos/README.md`](experimentos/README.md)). O experimento lê o dataset e as funções de `src/`, mas
não altera nada fora da própria pasta. **O que for adotado passa para `src/` por pull request**, com teste.

## Versões

- O número da versão fica em `src/versao.py` e segue [SemVer](https://semver.org/lang/pt-BR/): `0.MENOR.CORREÇÃO`
  enquanto o projeto não tiver um resultado publicado.
- Toda mudança que altera o dataset muda a versão, e o arquivo de saída leva a versão no nome
  (`dataset/escolas_rr_v0.1.0.csv`).
- Cada versão tem uma entrada no [`CHANGELOG.md`](CHANGELOG.md) e uma tag (`v0.1.0`), criada no `main` depois
  do merge.

## As regras que não se quebram

São as mesmas do `CLAUDE.md`, em linguagem simples. Se uma mudança precisar quebrar alguma, pare e converse
com o grupo antes.

1. **Os dados de origem não se alteram.** `dados/origem/` e `dados/cache/` são só leitura. Nada renomeia,
   corrige ou regrava esses arquivos; o sha256 do MANIFEST é o teste.
2. **Todo número vem de código.** Nenhum número é digitado à mão num documento, notebook ou slide. Se um número
   aparece, existe um script que o gera.
3. **Notebooks só mostram.** Uma célula de notebook lê, filtra e desenha. Conta, média, intervalo ou modelo
   ficam em `src/` ou num experimento, e o notebook lê o resultado gravado.
4. **Nada do futuro entra na previsão.** Para prever o ano t+1, só entra o que se sabia até o ano t. Qualquer
   ajuste (padronização, preenchimento de vazio, limiar) usa só os anos de treino.
5. **O alvo nunca entra como variável explicativa**, nem disfarçado: aprovação, reprovação e abandono do mesmo
   ano somam 100, então duas delas revelam a terceira.
6. **Não se escolhe variável olhando a correlação com o alvo.** A escolha vem do sentido da variável, da
   cobertura e da estabilidade, decidida antes de ver o resultado.
7. **Vazio não é zero.** Escola que não oferece a etapa não tem abandono 0: tem "não se aplica". Na dúvida, deixe
   vazio e registre.
8. **Teste se escreve antes de rodar.** A pergunta, a divisão dos anos, os modelos e a regra de leitura ficam no
   `docs/PROTOCOLO.md` antes da execução, que acontece uma vez. Resultado nulo também é resultado.
9. **Anos de teste já usados não escolhem nada.** Os anos que já serviram de teste (2016–2019 e 2021–2024) não
   servem para escolher modelo, variável ou limiar.
10. **Toda decisão fica registrada** no `docs/DECISOES.md`: o que foi decidido, por quê e onde está a evidência.

## Quando o repositório estiver no GitHub

Quem administra o repositório configura uma vez, em *Settings → Branches → Branch protection rules* para o
`main`: exigir pull request antes do merge, exigir 1 aprovação, impedir push direto e impedir que o autor aprove
o próprio pull request.

Se o repositório for privado num plano do GitHub que não aplica proteção de branch, a regra continua valendo
como combinado do grupo: ninguém faz push direto no `main`, e todo pull request é aprovado por outra pessoa antes
do merge.
