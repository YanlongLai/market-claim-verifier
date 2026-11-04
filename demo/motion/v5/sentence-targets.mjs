/** Named proof for every independent voice unit. Used by real-frame audits. */
export const targets={
 v500:{disclosure_origin:['.intro .wordmark','.intro h1','.intro .origin'],disclosure_build:['.disclosure']},
 v501:{post:['.post-original'],reposts:['.post-copy'],question:['.viral-headline'],period:['.post-original .apple-line','.post-original .post-focus'],stakes:['.viral-headline']},
 v502:{formats:['.asset-preview'],screenshot:['.input-tile:nth-child(1).lit'],pdf:['.input-tile:nth-child(2).lit'],podcast:['.input-tile:nth-child(3).lit'],video:['.input-tile:nth-child(4).lit'],question:['.inputs-question']},
 v503:{single:['.terminal-row.principal'],agent:['.terminal-row'],nine:['.terminal-row.principal'],heldout:['.terminal-row.principal']},
 v504:{model:['#node-1','#node-2'],program:['#node-3','#node-4'],principle:['.architecture [data-on-screen]']},
 v505:{live:['.live-overlay'],paste:['.live-overlay'],tools:['.live-terminal'],claims:['.live-terminal'],lookups:['.live-terminal'],evidence_ids:['.live-terminal'],thinking:['.live-terminal','.live-stopwatch','.live-terminal-line[data-kind="reasoning"]'],decide:['.live-terminal','.live-stopwatch'],verdict:['.live-overlay h2','.filing-citation[data-form="10-K"]','.filing-citation[data-form="10-Q"]'],draft:['.live-overlay'],evidence:['.live-overlay'],trace:['.live-overlay'],each:['.live-overlay'],program:['.live-overlay'],receipt:['.live-overlay']},
 v506:{run:['.terminal-row'],ocr:['.terminal-row'],asr:['.terminal-row'],median:['.terminal-row.principal'],projection:['.terminal-row.principal']},
 v507:{accuracy:['[data-metric="accuracy"]'],false_support:['[data-metric="false_support"]'],cost_time:['[data-metric="cost_time"]'],coverage:['.results-note']},
 v508:{filing:['.ending'],url:['.site-url']},v509:{credit:['.credit'],wordmark:['.outro .wordmark','.stamp-robot']},
};
export const requiredText={
 'v501/question':'Is it right?','v501/period':'$416.2 billion','v501/stakes':'move money.',
 'v502/question':'How do you check all of them?',
 'v503/single':'74/357 correct · 20.7%','v503/agent':'SEC tools + Python verdict',
 'v503/nine':'20.7% → 90.5%','v503/heldout':'240/266 held-out · 90.2%',
 'v504/principle':'Model proposes; program decides.',
 'v506/median':'median 6.8 s/post','v506/projection':'1,000 posts ≈ 2 h · 1 worker',
 'v507/accuracy':'90.2%','v507/false_support':'1/139','v507/cost_time':'$0.02',
 'v508/url':'hackathon.dappgo.com','v509/wordmark':'DappGo',
};
