# product_catalog_api
REST API JSON Python microservice which allows users to browse a product catalog and which automatically updates prices from the external offer service.
URL of external offer service is specified in env var called `OFFERS_API_BASE_URL` set in `docker-compose.yml`.
Application saves acquired token together with `OFFERS_API_BASE_URL` in DB for next application start. If you start application against
external service which does not match the URL in DB the application refuses to start and you need to manually remove the access token
from DB - all your product, offers and prices wil be deleted by ON DELETE CASCADE.


# Run

The easiest way to play with the project is:

```shell
$ docker-compose up
```

Then open [127.0.0.1/docs](127.0.0.1/docs) or [127.0.0.1/redoc](127.0.0.1/redoc), see the docs with all the examples and responses and start to play!

# Test

There are two types of tests implemented. Integration and unit tests:

### Unit tests - Run

Enter the `test/unit` directory and simply run pytest by command:
```shell
$ py.test
```

### Integration tests - Run

Run the containers in background by command:
```shell
$ docker-compose up -d
```
Then enter the `test/integration` directory and simply run pytest by command:
```shell
$ py.test
```
When you are done with the tests stop the application containers by command:
```shell
$ docker-compose down
```