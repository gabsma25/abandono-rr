# Previsão do ano seguinte (esqueleto)

**Quem:** João, Gustavo e Gabriela · **Branch:** um por issue (#15–#22) · **Estado:** em andamento

## A pergunta

Que variáveis os modelos de previsão do abandono de t+1 usam, e quanto elas concordam entre algoritmos e
recortes? Os rankings de variáveis saem de redes algoritmo–variável montadas a partir das importâncias por
permutação.

## O que se espera e como se vai ler

O esqueleto roda primeiro só com dados sintéticos (`sintetico.py`), em que as variáveis verdadeiras são
conhecidas, e só depois com os pares reais. O protocolo da execução real (anos, modelos, leitura) vai no
`docs/PROTOCOLO.md` antes de rodar; até lá o modo real fica bloqueado (#22).

## Como rodar

```bash
python -m experimentos.previsao_t1.sintetico       # pares.csv e importancias.csv sintéticos em saida/sintetico/
```

O formato dos arquivos que passam de uma parte para a outra está em [`CONTRATO.md`](CONTRATO.md), e o
`contrato.py` o confere.

## O que saiu

Ainda nada: o esqueleto está sendo montado.
