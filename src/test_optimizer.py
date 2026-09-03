from smart_route_optimizer import optimize_route


route, cost = optimize_route(
    traffic="High",
    weather="Rainy",
    delay_probability=1.0
)


print()
print("======================================")
print("       ROAD NETWORK ROUTE TEST")
print("======================================")

print()

print("Recommended Route:")

print(
    " -> ".join(route)
)

print()

print("Adjusted Route Cost:", cost)

print()

print("======================================")