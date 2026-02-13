> 💡 Question 1 : Dans la RFC 7231, nous trouvons que certaines méthodes HTTP sont considérées comme sûres (safe) ou idempotentes, en fonction de leur capacité à modifier (ou non) l'état de l'application. Lisez les sections 4.2.1 et 4.2.2 de la RFC 7231 et répondez : parmi les méthodes mentionnées dans l'activité 2, lesquelles sont sûres, non sûres, idempotentes et/ou non idempotentes?

> 💡 Question 2 : Décrivez l'utilisation de la méthode join dans ce cas. Utilisez les méthodes telles que décrites à Simple Relationship Joins et Joins to a Target with an ON Clause dans la documentation SQLAlchemy pour ajouter les colonnes demandées dans cette activité. Veuillez inclure le code pour illustrer votre réponse.

> 💡 Question 3 : Quels résultats avez-vous obtenus en utilisant l’endpoint POST /stocks/graphql-query avec la requête suggérée ? Veuillez joindre la sortie de votre requête dans Postman afin d’illustrer votre réponse.

`{{baseURL}}/stocks/graphql-query`

```
{
    "data": {
        "product": null
    },
    "errors": null
}
```

Rien parce que l'id dans le body est 1. changeons la a par exemple produit 13:
```
{
    "data": {
        "product": {
            "id": 13,
            "name": "Product 13",
            "quantity": 5
        }
    },
    "errors": null
}
```

> 💡 Question 4 : Quelles lignes avez-vous changé dans update_stock_redis? Veuillez joindre du code afin d’illustrer votre réponse.

Une opti aurai put etre faite ici mais je lai pas fait. Par exemple, jai du manuellement sync la metadata dans redis pour tout avec une nouvelle methode, et clear la cache manuellement.

> 💡 Question 5 : Quels résultats avez-vous obtenus en utilisant l’endpoint POST /stocks/graphql-query avec les améliorations ? Veuillez joindre la sortie de votre requête dans Postman afin d’illustrer votre réponse.


```
{
    "data": {
        "product": {
            "id": 13,
            "name": "Product 13",
            "quantity": 5
        }
    },
    "errors": null
}
```

Changeons la requete pour avoir les nouvelles colonnes:
{
  product(id: "13") {
    id
    name
    sku
    price
    quantity
  }
}

{
    "data": {
        "product": {
            "id": 13,
            "name": "Product 13",
            "price": 0.0,
            "quantity": 5,
            "sku": ""
        }
    },
    "errors": null
}


```
dusty@dusty-laptop:~/SchoolRepos/log430-labo3-mapleduck/scripts$ docker compose up
Attaching to supplier_app-1
supplier_app-1  | 2026-02-12 23:57:49,212 - INFO - Starting periodic calls to http://store_manager:5000/stocks/graphql-query every 10 seconds
supplier_app-1  | 2026-02-12 23:57:49,212 - INFO - Press Ctrl+C to stop
supplier_app-1  | 2026-02-12 23:57:49,213 - INFO - --- Call #1 ---
supplier_app-1  | 2026-02-12 23:57:49,213 - INFO - Calling http://store_manager:5000/stocks/graphql-query (attempt 1/3)
supplier_app-1  | 2026-02-12 23:57:49,219 - INFO - Response: 200 - OK
supplier_app-1  | 2026-02-12 23:57:49,219 - INFO - Response body: {"data":{"product":{"id":1,"name":"Laptop ABC","price":1999.99,"quantity":1991,"sku":"LP12567"}},"errors":null}
supplier_app-1  | ...
supplier_app-1  | 2026-02-12 23:57:49,219 - INFO - Waiting 10 seconds until next call...
Gracefully Stopping... press Ctrl+C again to force
```