import strawberry

# from graphql.mutations.auth import AuthMutation
from app_graphql.mutations.flights import AirportsMutation
# from graphql.queries.auth import AuthQuery
from app_graphql.queries.flights import AirportsQuery


@strawberry.type
class Query(AirportsQuery):
    pass


@strawberry.type
class Mutation(AirportsMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
