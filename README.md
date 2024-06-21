# forest-service

This service takes a PyQuil or Quil implementation as data or via an URL and returns either compiled circuit properties and the transpiled Quil String (Transpilation Request) or its results (Execution Request) depending on the input data and selected backend.


[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Setup
* Clone repository:
```
git clone https://github.com/UST-QuAntiL/forest-service.git 
git clone git@github.com:UST-QuAntiL/forest-service.git
```

* Start containers:
```
docker-compose pull
docker-compose up
```

Now the forest-service is available on http://localhost:5014/.

## After implementation changes
* Update container:
```
docker build -t planqk/forest-service:latest .
docker push planqk/forest-service:latest
```

* Start containers:
```
docker-compose pull
docker-compose up
```

## API Documentation
The qiskit-service provides a Swagger UI, specifying the request schemas and showcasing exemplary requests for all API endpoints.
* http://localhost:5014/api/swagger-ui

The OpenAPI specifications are also statically available:
[OpenAPI JSON](./docs/openapi.json)  
[OpenAPI YAML](./docs/openapi.yaml)

## Sample Implementations for Transpilation and Execution
Sample implementations can be found [here](https://github.com/UST-QuAntiL/nisq-analyzer-content/tree/master/compiler-selection/Shor).
Please use the raw GitHub URL as `impl-url` value (see [example](https://raw.githubusercontent.com/UST-QuAntiL/nisq-analyzer-content/master/compiler-selection/Shor/shor-fix-15-quil.quil)).

## Haftungsausschluss

Dies ist ein Forschungsprototyp.
Die Haftung für entgangenen Gewinn, Produktionsausfall, Betriebsunterbrechung, entgangene Nutzungen, Verlust von Daten und Informationen, Finanzierungsaufwendungen sowie sonstige Vermögens- und Folgeschäden ist, außer in Fällen von grober Fahrlässigkeit, Vorsatz und Personenschäden, ausgeschlossen.

## Disclaimer of Warranty

Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE.
You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under this License.
