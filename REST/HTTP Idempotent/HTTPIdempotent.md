- The following HTTP methods obey the idempotent rule.
GET
HEAD
PUT
DELETE

- Below HTTP methods do not support idempotent rule.
POST
PATCH






- Are REST web services stateless?
Yes, REST APIs are stateless. It does not preserve the session or the state of the client on the REST server. It does not save any client data, session, or information for any request. Every request whether it’s from the same client or from a different client executes independently.

RESTful web services could be restart between two API calls or requests without impacting response.
