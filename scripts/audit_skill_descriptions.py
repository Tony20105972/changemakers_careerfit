import json
from pathlib import Path
from collections import Counter, defaultdict

SKILL_DESC_PATH = Path("data/skill_descriptions.json")
TAXONOMY_PATH = Path("data/skill_taxonomy.json")

REQUIRED_FIELDS = [
    "label_ko",
    "definition",
    "person_profile",
    "workplace_behavior",
    "business_value",
    "career_relevance",
    "market_context",
    "strength_narrative",
    "gap_narrative",
    "development_direction",
    "summary_phrase",
    "keywords",
]

GENERIC_PHRASES = [
    "관련 지식을 알고 있는 수준을 넘어",
    "상황을 읽고 필요한 기준과 산출물로 연결해",
    "실제 조직의 흐름 안에서 다루는 능력",
    "특정 업무 경험 하나를 넘어",
    "시장 맥락의 신호가 됩니다",
    "더 선명하게 드러납니다",
]

ACTION_WORDS = [
    "향상시키세요",
    "수강",
    "자격 취득",
    "권장",
    "추천",
    "해야 합니다",
]


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def extract_taxonomy_keys(taxonomy):
    if isinstance(taxonomy, dict):
        if "skills" in taxonomy and isinstance(taxonomy["skills"], list):
            return {item["skill_key"] for item in taxonomy["skills"]}
        return set(taxonomy.keys())

    if isinstance(taxonomy, list):
        return {item["skill_key"] for item in taxonomy}

    raise TypeError("Unsupported taxonomy format")


def main():
    desc = load_json(SKILL_DESC_PATH)
    taxonomy = load_json(TAXONOMY_PATH)

    taxonomy_keys = extract_taxonomy_keys(taxonomy)
    desc_keys = set(desc.keys())

    missing_keys = sorted(taxonomy_keys - desc_keys)
    extra_keys = sorted(desc_keys - taxonomy_keys)

    missing_fields = defaultdict(list)
    empty_fields = defaultdict(list)
    short_fields = defaultdict(list)
    generic_hits = defaultdict(list)
    action_hits = defaultdict(list)
    phrase_counter = Counter()

    for skill_key, item in desc.items():
        for field in REQUIRED_FIELDS:
            if field not in item:
                missing_fields[skill_key].append(field)
                continue

            value = item[field]

            if field == "keywords":
                if not isinstance(value, list) or not value:
                    empty_fields[skill_key].append(field)
                continue

            if not isinstance(value, str) or not value.strip():
                empty_fields[skill_key].append(field)
                continue

            if len(value.strip()) < 40 and field not in {"label_ko", "summary_phrase"}:
                short_fields[skill_key].append(field)

            for phrase in GENERIC_PHRASES:
                if phrase in value:
                    generic_hits[skill_key].append(phrase)
                    phrase_counter[phrase] += 1

            for word in ACTION_WORDS:
                if word in value:
                    action_hits[skill_key].append(word)

    print("Skill Description Audit")
    print("=" * 40)
    print(f"taxonomy_count={len(taxonomy_keys)}")
    print(f"description_count={len(desc_keys)}")
    print(f"missing_skill_keys={len(missing_keys)}")
    print(f"extra_skill_keys={len(extra_keys)}")
    print(f"missing_fields_skills={len(missing_fields)}")
    print(f"empty_fields_skills={len(empty_fields)}")
    print(f"short_fields_skills={len(short_fields)}")
    print(f"generic_phrase_skills={len(generic_hits)}")
    print(f"action_word_skills={len(action_hits)}")

    if missing_keys:
        print("\nMissing skill keys:")
        print(missing_keys[:30])

    if extra_keys:
        print("\nExtra skill keys:")
        print(extra_keys[:30])

    if missing_fields:
        print("\nMissing fields sample:")
        for k, v in list(missing_fields.items())[:10]:
            print(k, v)

    if empty_fields:
        print("\nEmpty fields sample:")
        for k, v in list(empty_fields.items())[:10]:
            print(k, v)

    if short_fields:
        print("\nShort fields sample:")
        for k, v in list(short_fields.items())[:10]:
            print(k, v)

    if phrase_counter:
        print("\nRepeated generic phrases:")
        for phrase, count in phrase_counter.most_common():
            print(f"{count}x - {phrase}")

    if generic_hits:
        print("\nGeneric phrase skill sample:")
        for k, v in list(generic_hits.items())[:20]:
            print(k, sorted(set(v)))

    if action_hits:
        print("\nAction wording sample:")
        for k, v in list(action_hits.items())[:20]:
            print(k, sorted(set(v)))

    hard_fail = missing_keys or extra_keys or missing_fields or empty_fields
    quality_warn = short_fields or generic_hits or action_hits

    print("\nResult:")
    if hard_fail:
        print("FAIL: schema/key integrity issue")
        raise SystemExit(1)

    if quality_warn:
        print("WARN: quality improvement needed")
        raise SystemExit(0)

    print("PASS")


if __name__ == "__main__":
    main()