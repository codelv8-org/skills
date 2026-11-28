# AAA Fantasy Character Studio v2.0.0

**Release status: Beta.** Agent-native, cloud-first generation and validation of original semi-realistic Xianxia/Wuxia characters. The name describes the target art direction, not a certified AAA quality level.

## Use
Invoke `@AAA Fantasy Character Studio` or request “Create an original Xianxia sword immortal from this A-pose, using STRICT_AGENT_CLOUD, no external 3D API, with editable MeshIR and GLB.” Thai: “ปั้นตัวละครเซียนกระบี่ 3D จากภาพนี้ บน Cloud ไม่ใช้ Meshy/Tripo พร้อม GLB และหลักฐาน QA”. Input: text, reference images, multiview, or authorized mesh. Output: real editable geometry, source/IR, GLB and honest gate evidence; rig, materials and animation only when actually implemented and verified. Do not activate for image-only concepts, tactical characters, low-poly workflows or requests to use an external 3D generation service without authorization.

## Install
Download the catalog ZIP (built by the repository Pages workflow), extract the skill folder into your agent's supported skill directory, or run the repository's existing installer:

```sh
./scripts/install-skill.sh --skill aaa-fantasy-character-studio --agent codex
```

Use `--agent antigravity` or `--agent claude` for the corresponding agent. Windows: `.\scripts\install-skill.ps1 -Skill aaa-fantasy-character-studio -Agent codex`. Chat platforms: import the complete skill ZIP when supported. Check [SKILL.md](SKILL.md) and [agent-native.md](references/agent-native.md) before execution.

## Runtime and compatibility
Python 3.10+ standard library for the native compiler and diagnostic renderer. Requires verified agent-platform cloud execution and writable artifacts; no additional Python packages, external 3D SaaS, local GPU or local generation in STRICT_AGENT_CLOUD. CLOUD_DCC requires explicit opt-in; PLAN_ONLY if hosted execution is missing. Codex, Claude Code and Antigravity are compatible by design when configured for hosted execution, not certified across provider/model tiers. Gemini 4 Hydrogen+, GPT-6 Sol+ and Claude Opus 5.5+ are user-selected targets, not verified execution entitlements or benchmark results. Chat-side fixture execution tested; separate agent-platform execution NOT TESTED.

## Evidence and limitations
See the [native compiler fixture showcase](../../assets/examples/fantasy-character/native-compiler-v2/index.html) and [v1 diagnostic baseline](../../assets/examples/fantasy-character/index.html). v2 compiles an authored 18-triangle, 19-vertex fixture with two joints and one explicit animation, not a full humanoid. 26 unit tests pass. The prior v1 G1 blockout and the v2 compiler fixture are different scenarios; do not interpret these as a visual quality comparison. The existing v1 overview illustration is retained as concept art; refreshed v2 overview and matched full-character mode/version benchmarks are pending. No AAA, photoreal, production-ready or game-ready certification. See [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).
