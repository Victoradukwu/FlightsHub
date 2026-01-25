import strawberry

from app_graphql.mutations.auth import AuthMutations
from app_graphql.mutations.flights import FlightsMgtMutation
# from graphql.queries.auth import AuthQuery
from app_graphql.queries.flights import FlightsMgtQuery


@strawberry.type
class Query:
    @strawberry.field
    def flightsmgt_query(self) -> FlightsMgtQuery:
        return FlightsMgtQuery()


@strawberry.type
class Mutation:
    @strawberry.field
    def flightsmgt_mutation(self) -> FlightsMgtMutation:
        return FlightsMgtMutation()

    @strawberry.field
    def auth_mutation(self) -> AuthMutations:
        return AuthMutations()


schema = strawberry.Schema(query=Query, mutation=Mutation)

