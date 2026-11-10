/* Browser counterpart, verified against the Python engine on the same fixtures. */
const PosterSearch = (() => {
  const aliases=POSTER_SEARCH_CONFIG.aliases, controlled=new Set(POSTER_SEARCH_CONFIG.controlled);
  const keys=Object.keys(aliases).sort((a,b)=>b.length-a.length||(a<b?-1:a>b?1:0));
  function normalize(query) {
    const out=[],cjk=/^[\u3400-\u9fff]+$/,cjkKeys=keys.filter(k=>cjk.test(k)),memo=new Map();
    function splitCjk(token){
      if(!token)return [];
      if(memo.has(token))return memo.get(token);
      for(const key of cjkKeys)if(token.startsWith(key)){
        const rest=splitCjk(token.slice(key.length));
        if(rest!==null){const parts=[aliases[key],...rest];memo.set(token,parts);return parts;}
      }
      memo.set(token,null);return null;
    }
    const phraseWidth=Math.max(1,...keys.map(k=>k.split(/\s+/).length));
    for(const segment of query.toLowerCase().trim().split(/[,，;；|]+/)){
      const tokens=segment.split(/\s+/).filter(Boolean);let pos=0;
      while(pos<tokens.length){let found=false;
        for(let width=Math.min(phraseWidth,tokens.length-pos);width>0;width--){
          const phrase=tokens.slice(pos,pos+width).join(' ');
          if(Object.hasOwn(aliases,phrase)){out.push(aliases[phrase]);pos+=width;found=true;break;}
        }
        if(!found){const token=tokens[pos++],parts=cjk.test(token)?splitCjk(token):null;out.push(...(parts===null?[token]:parts));}
      }
    }
    return [...new Set(out)];
  }
  function tieKey(c,seed,words){
    const value=String(seed)+'\0'+words.join('\0')+'\0'+(c.source_url||'')+'\0'+c.id;
    let hash=2166136261;
    for(const byte of new TextEncoder().encode(value))hash=Math.imul(hash^byte,16777619)>>>0;
    return hash;
  }
  function fields(c){const o=c.observed,i=c.interpreted,v=c.color;return {
    'observed.visual_family':Object.values(o.visual_family).filter(Boolean),'observed.visual_driver':[o.visual_driver],
    'observed.composition':o.composition,'observed.text_density':[o.text_density],'interpreted.tone':i.tone,
    'interpreted.transferable_concepts':i.transferable_concepts.map(x=>x.id),'techniques':c.techniques,'typography':c.typography,
    'color.color_mode':[v.color_mode],'color.color_contrast':[v.color_contrast],'color.dominant_colors':v.dominant_colors,
    'original_use':[c.original_use],'art_history.term_id':c.art_history.map(x=>x.term_id),'art_history.relation':c.art_history.map(x=>x.relation)};}
  function facets(c){return {family:Object.values(c.observed.visual_family),history:c.art_history.map(x=>x.term_id),
    relation:c.art_history.map(x=>x.relation),composition:c.observed.composition,concept:c.interpreted.transferable_concepts.map(x=>x.id),
    driver:[c.observed.visual_driver],use:[c.original_use],status:[c.annotation_status]};}
  function passes(c,filters){const values=facets(c);for(const [k,v] of Object.entries(filters)){
    if(!(k in values))throw new Error('Unknown filter: '+k);
    if(v.length&&!v.some(x=>values[k].includes(x)))return false;}
    if(filters.history?.length&&filters.relation?.length)return c.art_history.some(h=>filters.history.includes(h.term_id)&&filters.relation.includes(h.relation));
    return true;}
  function search(cases,query='',options={}){
    const match=options.match||'any',diverse=!!options.diverse,limit=options.limit===undefined?8:options.limit;
    if(!['any','all'].includes(match))throw new Error('match must be any or all');
    const filters=Object.fromEntries(Object.entries(options.filters||{}).map(([k,v])=>[k,v.map(x=>aliases[x.toLowerCase()]||x.toLowerCase())]));
    const words=normalize(query),candidates=[];
    const seed=String(options.seed??''),usage=options.usage_counts||{},batch=new Set(options.batch_ids||[]),batchCases=cases.filter(c=>batch.has(c.id));
    for(const c of cases){if(!passes(c,filters))continue;const structured=fields(c);
      const free={id:c.id,title:c.title||'',creator:c.creator||'',year:c.year||'',original_subjects:c.original_subjects.join(' '),
        analysis:Object.entries(c.analysis).filter(([k])=>k!=='annotation_rationale').map(([,v])=>String(v)).join(' '),
        concept_reasons:c.interpreted.transferable_concepts.map(x=>x.reason||'').join(' ')};
      const matched=[],fieldNames=new Set();let score=0;
      for(const w of words){let hits,weight;
        if(controlled.has(w)){hits=Object.keys(structured).filter(k=>structured[k].includes(w));weight=2;}
        else{hits=Object.keys(free).filter(k=>free[k].toLowerCase().includes(w));weight=hits.some(k=>['id','title','creator'].includes(k))?4:1;}
        if(hits.length){matched.push(w);hits.forEach(k=>fieldNames.add(k));score+=weight;}}
      if(words.length&&(!matched.length||(match==='all'&&matched.length!==words.length)))continue;
      const counts=usage[c.id]||{},shown=counts.shown||0,used=counts.used||0,batchRepeat=batch.has(c.id);
      const overlap=Math.max(0,...batchCases.filter(b=>b.id!==c.id).map(b=>[...new Set(c.observed.composition)].filter(x=>b.observed.composition.includes(x)).length));
      const context=Math.min(shown,4)*.25+Math.min(used,4)*.5+2*Number(batchRepeat)+Math.min(overlap,3)*.25;
      candidates.push({row:{id:c.id,score,query_coverage:matched.length,query_terms:[...words],missing_terms:words.filter(w=>!matched.includes(w)),matched_terms:matched,matched_fields:[...fieldNames].sort(),family:c.observed.visual_family.primary,creator:c.creator??null,seed,recent_shown:shown,recent_used:used,batch_repeat:batchRepeat,batch_composition_overlap:overlap,context_penalty:context,tie_break:tieKey(c,seed,words)},c});
    }
    const compareId=(a,b)=>a<b?-1:a>b?1:0;
    candidates.sort((a,b)=>b.row.query_coverage-a.row.query_coverage||b.row.score-a.row.score||a.row.context_penalty-b.row.context_penalty||a.row.tie_break-b.row.tie_break||compareId(a.row.id,b.row.id));
    const chosen=[];
    while(candidates.length&&(limit===null||chosen.length<Math.max(0,limit))){let index=0;
      if(diverse){const coverage=candidates[0].row.query_coverage;
        const coveredTerms=new Set(chosen.flatMap(p=>p.row.matched_terms));
        const utility=item=>{let penalty=0;for(const p of chosen){
          penalty+=3*Number(!!item.row.creator&&item.row.creator===p.row.creator);
          penalty+=2*Number(!!item.row.family&&item.row.family===p.row.family);
          penalty+=.25*[...new Set(item.c.observed.composition)].filter(x=>p.c.observed.composition.includes(x)).length;}
          return [-item.row.matched_terms.filter(term=>!coveredTerms.has(term)).length,-item.row.score,penalty+item.row.context_penalty,item.row.tie_break];};
        for(let j=1;j<candidates.length&&candidates[j].row.query_coverage===coverage;j++){
          const a=utility(candidates[j]),b=utility(candidates[index]);
          if((a[0]-b[0]||a[1]-b[1]||a[2]-b[2]||a[3]-b[3]||compareId(candidates[j].row.id,candidates[index].row.id))<0)index=j;}}
      chosen.push(candidates.splice(index,1)[0]);
    }
    return chosen.map(x=>x.row);
  }
  return {normalize,search};
})();
