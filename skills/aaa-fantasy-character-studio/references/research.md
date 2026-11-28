# Research basis (2026-11-28)

Public workflow inspiration, not an implementation or reverse-engineering of proprietary models. No service calls, API keys, accounts or model weights are required by the strict path.

| Source | Observed approach | Adopted approach |
|---|---|---|
| Meshy [Text to 3D](https://docs.meshy.ai/en/api/text-to-3d) | Geometry preview then texture refinement; distinct smart-topology route | Freeze geometry first, generate editable topology, refine after review |
| Meshy [Post-processing](https://docs.meshy.ai/en/webapp/guides/choosing/post-processing) | Remesh, UV, texturing, rigging, animation, export | Explicit dependency gates G5-G11 |
| Meshy [AI integration](https://docs.meshy.ai/en/api/ai) | Modular generation and post-processing tool calls | Local-to-cloud tools with structured inputs and actual artifact outputs, not external APIs |
| Tripo [Multi-view](https://www.tripo3d.ai/product-doc/model-generation/multi-view-to-3d) | Matched pose, lighting, scale, angle | Reference consistency, fixed camera, uncertainty provenance |
| Tripo [Smart Mesh](https://www.tripo3d.ai/features/smart-mesh) | Topology budget, local edit | Quad-patch authoring, region-specific revision, preserve source |
| Tripo [Segmentation](https://www.tripo3d.ai/features/ai-model-segmentation) | Separate logical parts | Semantic part graph, module seams, stable IDs |
| Tripo [Feature overview](https://www.tripo3d.ai/help/getting-started/what-features-does-tripo-have) | UV, textures, rig, animation and export | Modular cloud stages, exact candidate QA |

Research: [TripoSG](https://arxiv.org/abs/2502.06608) uses trained rectified-flow transformers and SDF-based VAE with geometric supervision. [TripoSR](https://github.com/VAST-AI-Research/TripoSR) uses a trained single-image reconstruction model; its published GPU example is not an LLM code-only benchmark. [TripoSG code](https://github.com/VAST-AI-Research/TripoSG) specifies CUDA and at least 8 GB VRAM. Do not claim that prompt instructions reproduce these learned priors or quality. No bundled model checkpoints.

Model capability references: [Gemini 4 Hydrogen](https://deepmind.google/models/model-cards/gemini-4-hydrogen/), [OpenAI models](https://developers.openai.com/api/docs/models), [Claude Opus 5.5](https://www.anthropic.com/claude/opus). Agent reasoning/coding is not a native learned 3D decoder. Verify actual model/tool availability per session; there is no cross-provider certification or performance guarantee.
