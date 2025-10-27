Preciso que faça mudanças na aplicação.

# Mudanças na API:

Preciso que o consumo dos dados da API seja feito assincronamente.
Elas devem estar sempre em execução, com 5 tarefas em paralelo:

* Consumo e registro dos dados de corridas de 2022 até hoje;
* Consumo e registro dos dados de sprints de 2022 até hoje;
* Consumo e registro dos dados de classificações de 2022 até hoje;
* Consumo e registro dos dados de pontuação (pilotos e equipes) de 2022 até hoje;
* Consumo e registro dos dados de pneus de 2025 até hoje.

*Obs.:* Estes são os dados principais, mas quero que consuma e armazene todos os dados disponíveis de 2022 até hoje.

# Mudanças técnicas

* Banco de dados: O **.sqlite** deve ser substituído por um banco de dados mais robusto, como o *MySQL*.
* A API deve ser trocada para uma que permita o manuseio dos dados em um painel, como o Django.
* A página deve primeiro consumir os dados do Django, que caso ainda não tenham sido registrados, devem chamar as funções de consumo de dados.

# Mudanças visuais

* Preciso que crie uma página no framework mais bonito possível para que os dados acima sejam mostrados.
* Elabore gráficos, filtros, efeitos visuais e ui/ux da mais alta qualidade.
* Preciso que use as cores oficiais das equipes nos gráficos.
* Preciso que haja dois temas, um modo claro e um modo escuro, com as cores oficiais da Formula 1.
