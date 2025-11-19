#!/usr/bin/env python3
"""
Build Part 6: Neo4j Deep Dive & Interactive Query Playground
Addresses the critical missing feature: user can explore database!
"""

import json

def create_part6_cells():
    """Part 6: Neo4j Interactive Exploration"""
    cells = []

    # Part 6 Header
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "# PART 6: Neo4j Deep Dive & Query Playground\n",
            "\n",
            "**Time**: 15 minutes\n",
            "\n",
            "**Goals**:\n",
            "- Learn Cypher query language basics\n",
            "- Explore the database interactively\n",
            "- Run your own custom queries\n",
            "- Visualize query results\n",
            "- Understand the knowledge graph deeply\n",
            "\n",
            "**Your turn to explore!**"
        ]
    })

    # 6.1 Cypher Basics
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6.1 Cypher Query Language Basics"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 📖 Cypher: Graph Query Language\n",
            "\n",
            "Neo4j uses **Cypher** - an intuitive, ASCII-art style query language.\n",
            "\n",
            "**Core Concepts**:\n",
            "\n",
            "#### 1. Nodes (Entities)\n",
            "```cypher\n",
            "(n)              // Any node\n",
            "(s:Skill)        // Node with label 'Skill'\n",
            "(s:Skill {name: 'peek_door'})  // Node with properties\n",
            "```\n",
            "\n",
            "#### 2. Relationships (Connections)\n",
            "```cypher\n",
            "-[r]->           // Any relationship (directed)\n",
            "-[:CAN_USE]->    // Relationship with type\n",
            "-[r:CAN_USE {confidence: 0.9}]->  // With properties\n",
            "```\n",
            "\n",
            "#### 3. Patterns (Queries)\n",
            "```cypher\n",
            "(a)-[:KNOWS]->(b)  // Pattern: a knows b\n",
            "(a)-[:KNOWS*1..3]->(b)  // Path: 1-3 hops\n",
            "```\n",
            "\n",
            "#### 4. Common Clauses\n",
            "```cypher\n",
            "MATCH (n:Label)      // Find nodes\n",
            "WHERE n.prop > 5     // Filter\n",
            "RETURN n             // Return results\n",
            "ORDER BY n.prop DESC // Sort\n",
            "LIMIT 10             // Limit results\n",
            "```\n",
            "\n",
            "---\n",
            "\n",
            "### 📚 Example Queries for Our Database\n",
            "\"\"\"))\n",
            "\n",
            "if NEO4J_CONNECTED:\n",
            "    # Show example queries\n",
            "    examples = [\n",
            "        {\n",
            "            'description': '1. Get all skills',\n",
            "            'query': 'MATCH (s:Skill) RETURN s.name, s.kind, s.cost ORDER BY s.cost',\n",
            "            'explanation': 'Find all nodes labeled Skill, return their properties'\n",
            "        },\n",
            "        {\n",
            "            'description': '2. Find crisp (non-balanced) skills',\n",
            "            'query': \"MATCH (s:Skill) WHERE s.kind <> 'balanced' RETURN s.name, s.kind\",\n",
            "            'explanation': 'Filter skills where kind is NOT balanced'\n",
            "        },\n",
            "        {\n",
            "            'description': '3. Get procedural memories',\n",
            "            'query': 'MATCH (m:Memory)-[r:RECOMMENDS]->(s:Skill) RETURN m.context, s.name, r.confidence LIMIT 5',\n",
            "            'explanation': 'Find Memory-RECOMMENDS->Skill patterns'\n",
            "        },\n",
            "        {\n",
            "            'description': '4. Count nodes by label',\n",
            "            'query': 'MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC',\n",
            "            'explanation': 'Aggregate count of each node type'\n",
            "        }\n",
            "    ]\n",
            "    \n",
            "    for ex in examples:\n",
            "        print(\"\\n\" + \"=\"*70)\n",
            "        print(ex['description'])\n",
            "        print(\"=\"*70)\n",
            "        print(\"\\nQuery:\")\n",
            "        print(ex['query'])\n",
            "        print(\"\\nExplanation:\")\n",
            "        print(ex['explanation'])\n",
            "        print(\"\\nResults:\")\n",
            "        \n",
            "        try:\n",
            "            results = run_query(ex['query'])\n",
            "            if results:\n",
            "                df = pd.DataFrame(results)\n",
            "                display(df)\n",
            "            else:\n",
            "                print(\"  (No results)\")\n",
            "        except Exception as e:\n",
            "            print(f\"  Error: {e}\")\n",
            "else:\n",
            "    print(\"\\n⚠ Neo4j not connected. Examples shown conceptually.\")\n",
            "    print(\"\\nConnect to Neo4j to run live queries!\")"
        ]
    })

    # 6.2 Interactive Query Playground
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6.2 🎮 Interactive Query Playground"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 💻 Try Your Own Cypher Queries!\n",
            "\n",
            "**Suggested Queries to Try**:\n",
            "\n",
            "1. **All skills**: `MATCH (s:Skill) RETURN s`\n",
            "2. **High-cost skills**: `MATCH (s:Skill) WHERE s.cost > 1.5 RETURN s.name, s.cost`\n",
            "3. **Balanced skills only**: `MATCH (s:Skill {kind: 'balanced'}) RETURN s.name`\n",
            "4. **State transitions**: `MATCH (s1:State)-[r]->(s2:State) RETURN s1.name, type(r), s2.name`\n",
            "5. **Skill network**: `MATCH path = (s1:Skill)-[*1..2]-(s2:Skill) RETURN path LIMIT 5`\n",
            "\n",
            "**Tips**:\n",
            "- Start with simple `MATCH ... RETURN` queries\n",
            "- Use `LIMIT` to avoid huge results\n",
            "- Check syntax if you get errors\n",
            "- Neo4j is case-sensitive for labels!\n",
            "\"\"\"))\n",
            "\n",
            "# Interactive query widget\n",
            "query_text = widgets.Textarea(\n",
            "    value='MATCH (s:Skill) RETURN s.name, s.kind, s.cost ORDER BY s.cost',\n",
            "    placeholder='Enter Cypher query here...',\n",
            "    description='Cypher Query:',\n",
            "    style={'description_width': 'initial'},\n",
            "    layout=widgets.Layout(width='90%', height='100px')\n",
            ")\n",
            "\n",
            "run_query_button = widgets.Button(\n",
            "    description='Run Query',\n",
            "    button_style='success',\n",
            "    icon='play'\n",
            ")\n",
            "\n",
            "clear_button = widgets.Button(\n",
            "    description='Clear',\n",
            "    button_style='warning'\n",
            ")\n",
            "\n",
            "visualize_checkbox = widgets.Checkbox(\n",
            "    value=False,\n",
            "    description='Visualize as graph (if applicable)',\n",
            "    style={'description_width': 'initial'}\n",
            ")\n",
            "\n",
            "query_output = widgets.Output()\n",
            "\n",
            "def on_run_query(b):\n",
            "    with query_output:\n",
            "        clear_output(wait=True)\n",
            "        \n",
            "        query = query_text.value.strip()\n",
            "        \n",
            "        if not query:\n",
            "            print(\"⚠ Please enter a query!\")\n",
            "            return\n",
            "        \n",
            "        if not NEO4J_CONNECTED:\n",
            "            print(\"❌ Neo4j not connected!\")\n",
            "            print(\"   Start Neo4j: make neo4j-start\")\n",
            "            print(\"   Initialize DB: make init\")\n",
            "            return\n",
            "        \n",
            "        print(\"🔍 Running query...\")\n",
            "        print(\"=\" * 70)\n",
            "        print(query)\n",
            "        print(\"=\" * 70)\n",
            "        print()\n",
            "        \n",
            "        try:\n",
            "            results = run_query(query)\n",
            "            \n",
            "            if not results:\n",
            "                print(\"✓ Query succeeded but returned no results.\")\n",
            "                return\n",
            "            \n",
            "            print(f\"✓ Query returned {len(results)} result(s)\\n\")\n",
            "            \n",
            "            # Show as DataFrame\n",
            "            df = pd.DataFrame(results)\n",
            "            print(\"Results as Table:\")\n",
            "            display(df)\n",
            "            \n",
            "            # Optionally visualize\n",
            "            if visualize_checkbox.value:\n",
            "                print(\"\\nGraph Visualization:\")\n",
            "                \n",
            "                # Try to build graph from results\n",
            "                G_result = nx.DiGraph()\n",
            "                \n",
            "                # Look for node/relationship patterns\n",
            "                for row in results:\n",
            "                    # Try to find source/target pairs\n",
            "                    keys = list(row.keys())\n",
            "                    if len(keys) >= 2:\n",
            "                        src = str(row[keys[0]])\n",
            "                        dst = str(row[keys[1]])\n",
            "                        label = keys[2] if len(keys) > 2 else ''\n",
            "                        G_result.add_edge(src, dst, label=str(label))\n",
            "                \n",
            "                if G_result.number_of_nodes() > 0:\n",
            "                    plt.figure(figsize=(12, 8))\n",
            "                    pos = nx.spring_layout(G_result, k=1, iterations=50)\n",
            "                    nx.draw(G_result, pos, with_labels=True, \n",
            "                           node_color='lightblue', node_size=2000,\n",
            "                           font_size=10, font_weight='bold',\n",
            "                           arrows=True, edge_color='gray', width=2)\n",
            "                    \n",
            "                    if G_result.number_of_edges() < 20:  # Only show labels if not too many\n",
            "                        edge_labels = nx.get_edge_attributes(G_result, 'label')\n",
            "                        nx.draw_networkx_edge_labels(G_result, pos, edge_labels, font_size=8)\n",
            "                    \n",
            "                    plt.title('Query Result Graph', fontsize=14, fontweight='bold')\n",
            "                    plt.axis('off')\n",
            "                    plt.tight_layout()\n",
            "                    plt.show()\n",
            "                else:\n",
            "                    print(\"  (Results not suitable for graph visualization)\")\n",
            "        \n",
            "        except Exception as e:\n",
            "            print(f\"❌ Query Error: {e}\")\n",
            "            print(\"\\nCommon issues:\")\n",
            "            print(\"  - Check syntax (case-sensitive!)\")\n",
            "            print(\"  - Label or property doesn't exist\")\n",
            "            print(\"  - Missing RETURN clause\")\n",
            "\n",
            "def on_clear(b):\n",
            "    with query_output:\n",
            "        clear_output()\n",
            "    query_text.value = ''\n",
            "\n",
            "run_query_button.on_click(on_run_query)\n",
            "clear_button.on_click(on_clear)\n",
            "\n",
            "display(widgets.VBox([\n",
            "    query_text,\n",
            "    widgets.HBox([run_query_button, clear_button]),\n",
            "    visualize_checkbox\n",
            "]))\n",
            "display(query_output)\n",
            "\n",
            "display(Markdown(\"\"\"\n",
            "### 💡 Pro Tips\n",
            "\n",
            "**Explore the schema**:\n",
            "```cypher\n",
            "CALL db.labels()  // All node labels\n",
            "CALL db.relationshipTypes()  // All relationship types\n",
            "```\n",
            "\n",
            "**Find example of each type**:\n",
            "```cypher\n",
            "MATCH (n:Skill) RETURN n LIMIT 1\n",
            "```\n",
            "\n",
            "**Explore relationships**:\n",
            "```cypher\n",
            "MATCH (n)-[r]->(m) RETURN type(r) as rel_type, count(*) as count GROUP BY rel_type\n",
            "```\n",
            "\"\"\"))"
        ]
    })

    # 6.3 Common Query Patterns
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6.3 Common Query Patterns"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 📚 Query Pattern Library\n",
            "\n",
            "Here are some useful patterns for exploring the MacGyver MUD database:\n",
            "\"\"\"))\n",
            "\n",
            "patterns = [\n",
            "    {\n",
            "        'name': 'Filter by Property',\n",
            "        'query': 'MATCH (s:Skill) WHERE s.cost < 2.0 RETURN s.name, s.cost',\n",
            "        'use': 'Find low-cost skills'\n",
            "    },\n",
            "    {\n",
            "        'name': 'Aggregate Functions',\n",
            "        'query': 'MATCH (s:Skill) RETURN AVG(s.cost) as avg_cost, MAX(s.cost) as max_cost',\n",
            "        'use': 'Statistical summaries'\n",
            "    },\n",
            "    {\n",
            "        'name': 'Relationship Patterns',\n",
            "        'query': 'MATCH (a:Agent)-[:CAN_USE]->(s:Skill) RETURN a.name, s.name',\n",
            "        'use': 'Which skills can the agent use?'\n",
            "    },\n",
            "    {\n",
            "        'name': 'Path Finding',\n",
            "        'query': \"MATCH path = (start:State {name:'stuck_in_room'})-[:LEADS_TO*]->(end:State) WHERE 'escaped' IN end.name RETURN path LIMIT 3\",\n",
            "        'use': 'Find escape paths'\n",
            "    },\n",
            "    {\n",
            "        'name': 'Count Relationships',\n",
            "        'query': 'MATCH ()-[r:RECOMMENDS]->() RETURN count(r) as total_memories',\n",
            "        'use': 'How many procedural memories exist?'\n",
            "    },\n",
            "    {\n",
            "        'name': 'Property Exists',\n",
            "        'query': 'MATCH (s:Skill) WHERE exists(s.goal_fraction) RETURN s.name',\n",
            "        'use': 'Find balanced skills (have goal_fraction property)'\n",
            "    }\n",
            "]\n",
            "\n",
            "print(\"\\n📖 Query Pattern Library\\n\")\n",
            "for i, pattern in enumerate(patterns, 1):\n",
            "    print(\"=\" * 70)\n",
            "    print(f\"{i}. {pattern['name']}\")\n",
            "    print(\"=\" * 70)\n",
            "    print(f\"Use case: {pattern['use']}\")\n",
            "    print(f\"\\nQuery:\\n{pattern['query']}\")\n",
            "    print()\n",
            "\n",
            "display(Markdown(\"\"\"\n",
            "### 🎯 Try These Challenges\n",
            "\n",
            "Can you write queries to:\n",
            "\n",
            "1. Find the most expensive skill?\n",
            "2. Count how many balanced vs crisp skills exist?\n",
            "3. Find all observations that skills can produce?\n",
            "4. Get the agent's name and current state?\n",
            "5. Find which memories recommend 'peek_door'?\n",
            "\n",
            "Use the playground above to experiment!\n",
            "\"\"\"))"
        ]
    })

    # 6.4 Visualizing Query Results
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6.4 Advanced: Visualizing Complex Queries"]
    })

    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "display(Markdown(\"\"\"\n",
            "### 🎨 Create Custom Visualizations\n",
            "\n",
            "Example: Visualize the entire skill network with properties\n",
            "\"\"\"))\n",
            "\n",
            "if NEO4J_CONNECTED:\n",
            "    # Complex visualization example\n",
            "    skills_detailed = run_query(\"\"\"\n",
            "        MATCH (s:Skill)\n",
            "        OPTIONAL MATCH (s)-[r]->(o:Observation)\n",
            "        RETURN s.name as skill, \n",
            "               s.kind as kind, \n",
            "               s.cost as cost,\n",
            "               collect(o.name) as observations\n",
            "    \"\"\")\n",
            "    \n",
            "    if skills_detailed:\n",
            "        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))\n",
            "        \n",
            "        # Left: Skills by cost and kind\n",
            "        df_skills = pd.DataFrame(skills_detailed)\n",
            "        \n",
            "        crisp_skills = df_skills[df_skills['kind'] != 'balanced']\n",
            "        balanced_skills = df_skills[df_skills['kind'] == 'balanced']\n",
            "        \n",
            "        if not crisp_skills.empty:\n",
            "            ax1.barh(crisp_skills['skill'], crisp_skills['cost'], \n",
            "                    color='#3498db', alpha=0.7, label='Crisp')\n",
            "        if not balanced_skills.empty:\n",
            "            ax1.barh(balanced_skills['skill'], balanced_skills['cost'],\n",
            "                    color='#2ecc71', alpha=0.7, label='Balanced')\n",
            "        \n",
            "        ax1.set_xlabel('Cost', fontsize=12)\n",
            "        ax1.set_title('Skills by Cost', fontsize=14, fontweight='bold')\n",
            "        ax1.legend()\n",
            "        ax1.grid(axis='x', alpha=0.3)\n",
            "        \n",
            "        # Right: Skill counts by kind\n",
            "        kind_counts = df_skills['kind'].value_counts()\n",
            "        ax2.pie(kind_counts.values, labels=kind_counts.index, autopct='%1.1f%%',\n",
            "               colors=['#3498db', '#2ecc71', '#e74c3c'])\n",
            "        ax2.set_title('Skill Distribution by Kind', fontsize=14, fontweight='bold')\n",
            "        \n",
            "        plt.tight_layout()\n",
            "        plt.show()\n",
            "        \n",
            "        print(\"\\n📊 Skills Overview:\")\n",
            "        print(f\"  Total skills: {len(df_skills)}\")\n",
            "        print(f\"  Crisp skills: {len(crisp_skills)}\")\n",
            "        print(f\"  Balanced skills: {len(balanced_skills)}\")\n",
            "        print(f\"  Average cost: {df_skills['cost'].mean():.2f}\")\n",
            "    else:\n",
            "        print(\"⚠ No skills found in database.\")\n",
            "else:\n",
            "    print(\"⚠ Neo4j not connected.\")\n",
            "\n",
            "display(Markdown(\"\"\"\n",
            "### 🚀 What You Can Do\n",
            "\n",
            "With Neo4j and Cypher, you can:\n",
            "\n",
            "1. **Explore**: Query any part of the knowledge graph\n",
            "2. **Analyze**: Aggregate statistics and patterns\n",
            "3. **Visualize**: Create custom graphs and charts\n",
            "4. **Learn**: Understand how data is structured\n",
            "5. **Experiment**: Test new queries and relationships\n",
            "\n",
            "**Neo4j is your window into the agent's world!**\n",
            "\"\"\"))"
        ]
    })

    # Part 6 Summary
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "---\n",
            "\n",
            "### 🎯 Part 6 Summary\n",
            "\n",
            "**What we learned**:\n",
            "\n",
            "1. ✅ **Cypher basics** - Query language syntax and patterns\n",
            "2. ✅ **Interactive playground** - Run your own queries!\n",
            "3. ✅ **Common patterns** - Useful query templates\n",
            "4. ✅ **Visualization** - Turn queries into graphs and charts\n",
            "5. ✅ **Database exploration** - Full access to knowledge graph\n",
            "\n",
            "### 💡 Key Takeaways\n",
            "\n",
            "- **Cypher is intuitive**: ASCII-art style patterns\n",
            "- **Graph structure matters**: Relationships enable powerful queries\n",
            "- **Exploration is easy**: Try queries without breaking anything\n",
            "- **Visualization helps**: See patterns in the data\n",
            "\n",
            "### 🔗 Connection to Active Inference\n",
            "\n",
            "The knowledge graph stores:\n",
            "- **Skills** → What the agent can do\n",
            "- **States** → Where the agent can be\n",
            "- **Observations** → What the agent perceives\n",
            "- **Memories** → What the agent has learned\n",
            "\n",
            "All of this enables the agent to:\n",
            "1. Plan (find paths)\n",
            "2. Reason (query relationships)\n",
            "3. Learn (store experiences)\n",
            "4. Adapt (update beliefs)\n",
            "\n",
            "**The graph IS the agent's knowledge!**\n",
            "\n",
            "---\n",
            "\n",
            "**Next**: Back to our journey... we've seen execution and explored the database. Now let's understand strategies geometrically with the Silver Gauge!"
        ]
    })

    return cells


def append_part6_to_notebook(notebook_path):
    """Append Part 6 after Part 5"""
    with open(notebook_path, 'r') as f:
        nb = json.load(f)

    # Find where to insert (after Part 5, before final summary)
    insert_idx = None
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown':
            content = ''.join(cell['source'])
            if 'FINAL SUMMARY' in content or '🎓 FINAL SUMMARY' in content:
                insert_idx = i
                break

    if insert_idx is None:
        # Append at end if no summary found
        insert_idx = len(nb['cells'])

    part6_cells = create_part6_cells()
    nb['cells'] = nb['cells'][:insert_idx] + part6_cells + nb['cells'][insert_idx:]

    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=1)

    print(f"✓ Inserted {len(part6_cells)} cells for Part 6 at position {insert_idx}")


if __name__ == "__main__":
    notebook_path = "/home/juancho/macgyver_mud/MacGyverMUD_DeepDive.ipynb"

    print("Creating Part 6: Neo4j Deep Dive & Interactive Query Playground...")
    print("This addresses the CRITICAL MISSING FEATURE!")

    append_part6_to_notebook(notebook_path)

    print("\\n✓ Part 6 added successfully!")
    print("  - Cypher query language basics")
    print("  - Interactive query playground (YOUR OWN QUERIES!)")
    print("  - Common query patterns")
    print("  - Visualization of query results")
    print("  - Full database exploration capability")
