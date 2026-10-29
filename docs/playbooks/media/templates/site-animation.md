# Variant: looping website animation

Same roles and review rules; replace the video gates with:
1. Design note (placement, scene, motion, real data, a11y) → Owner OK.
2. Builder implements in a branch with a deterministic seek hook (`window.__scene.seek(t)` and `?t=` param),
   reduced-motion static fallback, pause when off-screen, EN/other-language strings, light/dark tokens.
3. Director checks with the seek hook at exact moments: desktop 1280 (dark + light), phone 375, each language,
   reduced motion; console errors; no horizontal scroll.
4. Fix loop until all pass → screenshots to Owner → merge and publish on Owner OK.
AI art only for textures/illustration; any words are real text.
