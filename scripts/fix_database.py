#!/usr/bin/env python3
"""
Quick database fix: Add missing observations and verify setup.
"""
from neo4j import GraphDatabase
import config

def fix_database():
    """Add missing observations and verify all skills exist."""

    driver = GraphDatabase.driver(
        config.NEO4J_URI,
        auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
    )

    try:
        with driver.session(database="neo4j") as session:
            print("=" * 60)
            print("DATABASE FIX - Adding Missing Observations")
            print("=" * 60)

            # Add missing observations
            observations = [
                ('obs_partial_info', 'Door appears to be in uncertain state'),
                ('obs_attempted_open', 'Door was tested but outcome unclear'),
                ('obs_strategic_escape', 'Escaped after gathering some information')
            ]

            for name, desc in observations:
                result = session.run('''
                    MERGE (o:Observation {name: $name})
                    SET o.description = $desc,
                        o.created_at = datetime()
                    RETURN o.name AS name
                ''', name=name, desc=desc)

                record = result.single()
                if record:
                    print(f"✓ {record['name']}")

            print("\nVerifying all observations:")
            result = session.run('MATCH (o:Observation) RETURN o.name AS name ORDER BY o.name')
            obs_names = [record['name'] for record in result]
            print(f"  Total: {len(obs_names)} observations")
            for obs in obs_names:
                print(f"    - {obs}")

            print("\nVerifying all skills:")
            result = session.run('''
                MATCH (s:Skill)
                RETURN s.name AS name, s.kind AS kind, s.cost AS cost
                ORDER BY s.kind, s.cost
            ''')

            skills = list(result)
            print(f"  Total: {len(skills)} skills")
            crisp_count = sum(1 for s in skills if s['kind'] in ['sense', 'act'])
            balanced_count = sum(1 for s in skills if s['kind'] == 'balanced')
            print(f"    Crisp: {crisp_count}")
            print(f"    Balanced: {balanced_count}")

            for skill in skills:
                print(f"    - {skill['name']:<25} {skill['kind']:<10} ${skill['cost']:.2f}")

            print("\n" + "=" * 60)
            print("DATABASE FIX COMPLETE")
            print("=" * 60)

    finally:
        driver.close()

if __name__ == '__main__':
    fix_database()
