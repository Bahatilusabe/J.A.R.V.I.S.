import random
from ai_core.co_evolution import (
    AttackerGenome,
    DefenseGenome,
    DetectionConfiguration,
    DetectionMethod,
    ResponseConfiguration,
    ResponseStrategy,
    MutationSimulator,
    PayloadCharacteristics,
)


def test_mutate_attacker_records_history():
    random.seed(42)
    sim = MutationSimulator(mutation_rate=1.0)
    ag = AttackerGenome()
    ag.tactics = []
    before_count = ag.mutation_count

    mutated = sim.mutate_attacker(ag, intensity=1.0)

    assert mutated.mutation_count == before_count + 1
    assert sim.mutation_history, "mutation_history should have at least one record"
    last = sim.mutation_history[-1]
    assert last["genome_type"] == "attacker"
    assert last["parent_id"] == ag.genome_id
    assert last["child_id"] == mutated.genome_id


def test_crossover_attackers_creates_offspring():
    random.seed(1)
    sim = MutationSimulator()
    p1 = AttackerGenome()
    p2 = AttackerGenome()
    p1.payload.size_bytes = 1000
    p2.payload.size_bytes = 3000

    children = sim.crossover_attackers(p1, p2)
    assert len(children) == 2
    c1, c2 = children
    assert p1.genome_id in c1.parent_genome_ids
    assert p2.genome_id in c1.parent_genome_ids
    # payload average
    assert c1.payload.size_bytes == (p1.payload.size_bytes + p2.payload.size_bytes) // 2
    # history should have entries for crossover
    assert any(r["mutation_type"] == "crossover" and r["genome_type"] == "attacker" for r in sim.mutation_history)


def test_mutate_defense_records_history():
    random.seed(3)
    sim = MutationSimulator(mutation_rate=1.0)
    dg = DefenseGenome()
    before_count = dg.mutation_count

    mutated = sim.mutate_defense(dg, intensity=1.0)

    assert mutated.mutation_count == before_count + 1
    assert sim.mutation_history, "mutation_history should have at least one record"
    last = sim.mutation_history[-1]
    assert last["genome_type"] == "defense"
    assert last["parent_id"] == dg.genome_id
    assert last["child_id"] == mutated.genome_id


def test_crossover_defenses_creates_offspring():
    random.seed(5)
    sim = MutationSimulator()
    p1 = DefenseGenome()
    p2 = DefenseGenome()
    p1.detection_config.sensitivity_level = 0.2
    p2.detection_config.sensitivity_level = 0.8

    children = sim.crossover_defenses(p1, p2)
    assert len(children) == 2
    c1, c2 = children
    assert p1.genome_id in c1.parent_genome_ids
    assert p2.genome_id in c1.parent_genome_ids
    # sensitivity averaged
    assert c1.detection_config.sensitivity_level == (p1.detection_config.sensitivity_level + p2.detection_config.sensitivity_level) / 2
    assert any(r["mutation_type"] == "crossover" and r["genome_type"] == "defense" for r in sim.mutation_history)
