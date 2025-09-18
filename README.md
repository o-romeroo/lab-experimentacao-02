# LAB02: Estudo das Características de Qualidade em Sistemas Java
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main)

### Visão Geral
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#visão-geral)
Este repositório contém o código, scripts e documentação do **Laboratório 02 de Experimentação de Software** do curso de Engenharia de Software.  
O objetivo principal é analisar as **características de qualidade interna** de sistemas open-source escritos em **Java**, correlacionando métricas de produto (calculadas pela ferramenta CK) com aspectos do processo de desenvolvimento dos repositórios.

Para isso, coletaremos dados de **1.000 repositórios Java mais populares do GitHub**, processaremos os resultados e analisaremos como popularidade, maturidade, atividade e tamanho dos repositórios se relacionam com métricas de qualidade como acoplamento, profundidade de herança e coesão.

---

### Questões de Pesquisa
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#questões-de-pesquisa)
Este laboratório abordará as seguintes questões de pesquisa:

- **RQ 01:** Qual a relação entre a popularidade dos repositórios e suas características de qualidade?
- **RQ 02:** Qual a relação entre a maturidade dos repositórios e suas características de qualidade?
- **RQ 03:** Qual a relação entre a atividade dos repositórios e suas características de qualidade?
- **RQ 04:** Qual a relação entre o tamanho dos repositórios e suas características de qualidade?

---

### Métricas
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#métricas)
As métricas utilizadas estão divididas em duas categorias:

**Métricas de processo**
- Popularidade: número de estrelas
- Tamanho: linhas de código (LOC) e linhas de comentários
- Atividade: número de releases
- Maturidade: idade do repositório em anos

**Métricas de qualidade (via CK)**  
- **CBO (Coupling Between Objects):** mede o grau de acoplamento entre classes
- **DIT (Depth Inheritance Tree):** avalia a profundidade da hierarquia de herança
- **LCOM (Lack of Cohesion of Methods):** mede a coesão das classes

---

### Processo de Desenvolvimento
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#processo-de-desenvolvimento)
O processo de desenvolvimento deste laboratório foi dividido em duas entregas:

- Lab02S01: Lista dos 1.000 repositórios Java + Script de automação de clone e coleta de métricas + Arquivo .csv com o resultado das medições de 1 repositório.
- Lab02S02: Arquivo .csv consolidado com todas as medições dos 1.000 repositórios + hipóteses + Análise e visualização de dados + elaboração do relatório final.

---

### Relatório Final
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#relatório-final)
O resultado completo do estudo, incluindo estatísticas descritivas, testes de correlação (Spearman/Pearson) e hipóteses discutidas, está consolidado no relatório final disponível no link abaixo:

[Relatório Final](https://github.com/o-romeroo/lab-experimentacao-02/tree/main/docs/RelatorioFinalLab02-VersaoFinal.pdf)

---

### Setup
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#setup)
- Linguagem: Python 3.12.2
- API: GitHub REST API
- Ferramentas: CK (métricas Java), Pandas (tratamento de dados)

---

### Contributing
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#contributing)
Este projeto é desenvolvido por **[João Vitor Romero e Lucas Randazzo]**. Contribuições são bem-vindas, porém solicitamos contato prévio antes de propor mudanças significativas.

---

### Referências
[](https://github.com/o-romeroo/lab-experimentacao-02/tree/main#referências)
- [Link para o cronograma do laboratório](https://github.com/joaopauloaramuni/laboratorio-de-experimentacao-de-software/tree/main/CRONOGRAMA)


