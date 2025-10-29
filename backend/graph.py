from langgraph.graph import StateGraph, START, END

def build_graph(OverallState, sentiment_node, design_node, policy_node, classifier_node):
    builder = StateGraph(OverallState)
    builder.add_node("classifier", classifier_node)
    builder.add_node("sentiment", sentiment_node)
    builder.add_node("design", design_node)
    builder.add_node("policy", policy_node)

    def route_from_classifier(state):
        return state["next"]

    builder.add_edge(START, "classifier")
    builder.add_conditional_edges("classifier", route_from_classifier, {
        "sentiment": "sentiment",
        "design": "design",
        "policy": "policy",
    })
    builder.add_edge("sentiment", END)
    builder.add_edge("design", END)
    builder.add_edge("policy", END)

    return builder
