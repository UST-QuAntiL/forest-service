from flask_smorest import Blueprint

from app import routes
from app.model.circuit_response import (
    ExecuteResponseSchema
)
from app.model.algorithm_request import (
    ExecuteRequest,
    ExecuteRequestSchema
)

blp = Blueprint(
    "Execute",
    __name__,
    description="Send implementation, input, QPU information, and your access token to the API to "
                "execute your circuit and get the result.",
)


@blp.route("/forest-service/api/v1.0/execute", methods=["POST"])
@blp.doc(description="*Note*: \"token\" should either be in \"input-params\" or extra. Both variants are combined "
                     "here for illustration purposes. *Note*: \"url\", \"hub\", \"group\", \"project\" are optional "
                     "such that otherwise the standard values are used.")
@blp.arguments(
    ExecuteRequestSchema,
    description='''\
                Execution via URL:
                    \"impl-url\": \"URL-OF-IMPLEMENTATION\" 
                Execution via data:
                    \"impl-data\": \"BASE64-ENCODED-IMPLEMENTATION\"
                Execution via transpiled Quil String:
                    \"transpiled-quil\":\"TRANSPILED-QUIL-STRING\" 
                for Batch Execution of multiple circuits use:
                    \"impl-url\": [\"URL-OF-IMPLEMENTATION-1\", \"URL-OF-IMPLEMENTATION-2\"]
                the \"input-params\"are of the form:
                    \"input-params\": {
                        \"PARAM-NAME-1\": {
                            \"rawValue\": \"YOUR-VALUE-1\",
                            \"type\": \"Integer\"
                        },
                        \"PARAM-NAME-2\": {
                            \"rawValue\": \"YOUR-VALUE-2\",
                            \"type\": \"String\"
                        },
                        ...
                        \"token\": {
                            \"rawValue\": \"YOUR-IBMQ-TOKEN\",
                            \"type\": \"Unknown\"
                        }
                    }''',
    example={
        "impl-url": "https://raw.githubusercontent.com/UST-QuAntiL/nisq-analyzer-content/master/example-implementations/Grover-SAT/grover-fix-sat-pyquil.py",
        "qpu-name": "qvm",
        "impl-language": "pyquil",
        "token": "YOUR-TOKEN",
        "input-params": {}
    }
)
@blp.response(200, ExecuteResponseSchema, description="Returns a content location for the result. Access it via GET")
def encoding(json: ExecuteRequest):
    if json:
        return routes.execute_circuit()
