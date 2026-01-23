import strawberry

# from graphql.mutations.auth import AuthMutation
from app_graphql.mutations.flights import AirlinesMutation, AirportsMutation
# from graphql.queries.auth import AuthQuery
from app_graphql.queries.flights import AirlinesQuery, AirportsQuery


@strawberry.type
class Query(AirlinesQuery, AirportsQuery):
    pass


@strawberry.type
class Mutation(AirlinesMutation, AirportsMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)

