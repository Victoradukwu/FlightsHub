import strawberry

# from graphql.queries.auth import AuthQuery
from app_graphql.queries.flights import FlightsQuery

# from graphql.mutations.auth import AuthMutation
# from graphql.mutations.flights import FlightMutation

@strawberry.type
class Query(FlightsQuery):
    pass

# @strawberry.type
# class Mutation(AuthMutation, FlightMutation):
#     pass

schema = strawberry.Schema(
    query=Query,
    # mutation=Mutation,
)
