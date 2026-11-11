# Como contribuir

Somos três pessoas trabalhando no mesmo repositório, em máquinas diferentes. Este guia existe para que
ninguém quebre o trabalho de ninguém e para que todo número do projeto continue tendo uma origem verificável.

## O fluxo, passo a passo

1. **Atualize o `main`** antes de começar: `git switch main` e `git pull`.
2. **Crie um branch por tarefa**, com um nome curto que diga o que é:
   `git switch -c dataset-matriculas`, `git switch -c corrige-funil-2025`, `git switch -c exp-historico-encolhido`.
   Uma tarefa = um branch. Não junte duas coisas sem relação no mesmo branch.
3. **Trabalhe e faça commits pequenos**, no padrão da seção abaixo.
4. **Antes de abrir o pull request, rode `python rodar_tudo.py`.** Ele regera tudo e roda os testes. Só abra o
   pull request com os testes passando. Se um teste aparecer como pulado (`skipped`), leia o motivo: quase sempre
   são os zips do INEP que faltam na sua máquina (`python -m src.aquisicao --origem-local PASTA`).
5. **Abra o pull request para o `main`** e preencha o modelo (o que muda, como foi testado, o que pode afetar).
6. **Outra pessoa revisa.** Ninguém aprova o próprio pull request. Quem revisa lê o código, roda
   `python rodar_tudo.py` no branch e confere se os números que mudaram têm explicação.
7. **Só depois da aprovação** o pull request entra no `main`.

**O `main` só recebe mudanças por pull request revisado por outra pessoa.** Ninguém faz commit nem push direto
no `main`, nem para corrigir uma vírgula.

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
