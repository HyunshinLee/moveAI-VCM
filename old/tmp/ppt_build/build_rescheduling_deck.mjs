import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "/Users/drew/Documents/ChatGPT/해커톤/moveAI-VCM/Re-scheduling_알고리즘_설명자료.pptx";
const PREVIEW = "/Users/drew/Documents/ChatGPT/해커톤/moveAI-VCM/tmp/ppt_build/rendered";
const C = { navy:"#10069F", navy2:"#08045F", gold:"#91723A", dark:"#202124", gray:"#6F6F6F", mid:"#CFCFCF", light:"#F2F2F2", white:"#FFFFFF", red:"#C63C32", green:"#23825F", blueLight:"#E8E8FA", goldLight:"#F2EBDD" };
const deck = Presentation.create({ slideSize:{width:1280,height:720} });

function shape(slide, x,y,w,h, fill=C.white, radius=true, line="none") {
  return slide.shapes.add({geometry:radius?"roundRect":"rect", position:{left:x,top:y,width:w,height:h}, fill, line:{style:"solid",fill:line,width:line==="none"?0:1.2}, borderRadius:radius?"rounded-lg":undefined});
}
function text(slide, value, x,y,w,h, size=22, color=C.dark, bold=false, align="left") {
  const s=slide.shapes.add({geometry:"textbox",position:{left:x,top:y,width:w,height:h},fill:"none",line:{style:"solid",fill:"none",width:0}});
  s.text=value; s.text.style={fontSize:size,color,bold,alignment:align,fontFamily:"Arial"}; return s;
}
function title(slide, value, kicker="RE-SCHEDULING ENGINE") {
  text(slide,kicker,64,34,360,24,13,C.gold,true);
  text(slide,value,64,66,1150,55,36,C.dark,true);
  shape(slide,64,130,1152,3,C.navy,false);
}
function footer(slide,n){ text(slide,`MOVE AI · VCM   |   ${String(n).padStart(2,"0")}`,64,684,1150,18,11,C.gray,false,"right"); }
function note(slide, extra="") { slide.speakerNotes.textFrame.setText(`[Sources]\n- Karam & Reinau (2022), A Real-Time Decision Support Approach for Managing Disruptions in Line-Haul Freight Transport Networks.\n- MOVE AI VCM team algorithm specification and delivery-only operating assumptions.\n${extra}`); }
function arrow(slide,a,b,from="right",to="left",color=C.navy){ slide.shapes.connect(a,b,{kind:"elbow",fromSide:from,toSide:to,line:{style:"solid",fill:color,width:2.5},tail:{type:"arrow",width:"med",length:"med"}}); }
function node(slide,label,x,y,w=180,h=62,fill=C.white,color=C.dark,stroke=C.mid){ const s=shape(slide,x,y,w,h,fill,true,stroke); text(slide,label,x+10,y+12,w-20,h-20,18,color,true,"center"); return s; }
function bullet(slide,head,body,x,y,w){ text(slide,head,x,y,w,28,22,C.navy,true); text(slide,body,x,y+34,w,58,17,C.gray,false); }

// 1
{
 const s=deck.slides.add(); s.background.fill=C.navy2;
 text(s,"실시간 도로 변화에 대응하는",70,138,800,52,28,C.gold,true);
 text(s,"Re-scheduling 알고리즘",70,194,1030,86,54,C.white,true);
 text(s,"고객 순서는 유지할 것인가, 바꿀 것인가, 차량을 추가할 것인가",72,302,900,40,22,"#D8D8EE",false);
 shape(s,72,398,1080,2,C.gold,false);
 text(s,"Detour  ·  Re-route  ·  New truck",72,430,800,40,26,C.white,true);
 text(s,"Delivery-only 운영 모델 | TDVRP 결과 + Updated road graph",72,608,900,30,16,"#B9B9D5",false);
 note(s);
}

// 2
{
 const s=deck.slides.add(); title(s,"도로가 바뀌면 먼저 ‘영향이 있는지’부터 판단한다");
 const a=node(s,"TDVRP 최종 순서",70,185,190,70,C.blueLight,C.navy,C.navy);
 const b=node(s,"차량 현재 상태",70,315,190,70,C.white,C.dark,C.mid);
 const c=node(s,"Updated graph",70,445,190,70,C.goldLight,C.gold,C.gold);
 const d=node(s,"기존 계획 재평가",360,315,210,80,C.navy,C.white,C.navy);
 const e=node(s,"허용 지연 초과?\n경로 단절?",670,315,210,80,C.white,C.dark,C.navy);
 const f=node(s,"기존 계획 유지",990,205,190,70,C.light,C.gray,C.mid);
 const g=node(s,"3개 대안 생성",990,425,190,70,C.gold,C.white,C.gold);
 arrow(s,a,d); arrow(s,b,d); arrow(s,c,d); arrow(s,d,e); arrow(s,e,f,"right","left",C.gray); arrow(s,e,g,"right","left",C.gold);
 text(s,"NO",910,235,50,22,14,C.gray,true,"center"); text(s,"YES",910,446,50,22,14,C.gold,true,"center");
 text(s,"완료된 고객과 현재 주행 구간은 고정하고, 남은 계획만 다시 계산",350,550,650,34,20,C.navy,true,"center"); footer(s,2); note(s);
}

// 3
{
 const s=deck.slides.add(); title(s,"No-action은 실행안이자 모든 개선 효과의 기준선이다");
 shape(s,70,175,480,390,C.light,true,"none");
 text(s,"기존 계획을 그대로 수행",105,215,390,36,27,C.navy,true);
 bullet(s,"통행 가능","현재 속도로 기존 상세 경로를 진행",105,290,380);
 bullet(s,"완전 통제","통제 해제까지 대기한 뒤 진행",105,395,380);
 const n1=node(s,"초기 예상 도착",660,220,190,70,C.white,C.dark,C.mid);
 const n2=node(s,"장애 후 예상 도착",940,220,210,70,C.goldLight,C.gold,C.gold);
 arrow(s,n1,n2);
 text(s,"다른 대안의 효과",660,355,490,34,25,C.dark,true);
 text(s,"지연 절감 = No-action 지연 − 대안 지연\n추가 비용 = 대안 비용 − No-action 비용",660,410,500,90,21,C.gray,false);
 footer(s,3); note(s);
}

// 4
{
 const s=deck.slides.add(); title(s,"Detour는 고객 순서를 유지하고 도로만 우회한다");
 text(s,"고객 sequence",72,168,220,30,20,C.gray,true);
 const seq=[]; ["현재 위치","고객 A","고객 B","종료 Depot"].forEach((v,i)=>seq.push(node(s,v,72+i*280,215,175,60,i===0?C.blueLight:C.white,i===0?C.navy:C.dark,i===3?C.gold:C.mid)));
 for(let i=0;i<3;i++) arrow(s,seq[i],seq[i+1]);
 shape(s,400,308,220,5,C.red,false); text(s,"고객 순서는 변경하지 않음",435,326,360,28,18,C.red,true);
 const p1=node(s,"폐쇄 arc 제거",120,440,185,65,C.light,C.dark,C.mid);
 const p2=node(s,"Live 통행시간 적용",390,440,210,65,C.light,C.dark,C.mid);
 const p3=node(s,"최단시간 경로 탐색",690,440,220,65,C.navy,C.white,C.navy);
 const p4=node(s,"상세 waypoint 반환",1000,440,200,65,C.gold,C.white,C.gold);
 arrow(s,p1,p2); arrow(s,p2,p3); arrow(s,p3,p4);
 text(s,"적합: 대체 도로가 있고 고객 약속·배정 변경을 최소화해야 할 때",130,570,1020,34,20,C.navy,true,"center"); footer(s,4); note(s);
}

// 5
{
 const s=deck.slides.add(); title(s,"Detour는 각 고객 사이를 시간의존 최단경로로 연결한다");
 const a=node(s,"다음 목적지 선택",80,190,190,64,C.white,C.dark,C.mid);
 const b=node(s,"폐쇄 제거 +\n속도 가중치 갱신",350,190,210,74,C.blueLight,C.navy,C.navy);
 const c=node(s,"TD Dijkstra",650,190,190,64,C.navy,C.white,C.navy);
 const d=node(s,"경로 존재?",930,190,180,64,C.white,C.dark,C.navy);
 arrow(s,a,b); arrow(s,b,c); arrow(s,c,d);
 const e=node(s,"상세 path 저장",930,340,180,64,C.goldLight,C.gold,C.gold);
 const f=node(s,"Detour 불가",650,340,190,64,"#F9E5E3",C.red,C.red);
 arrow(s,d,e,"bottom","top",C.gold); arrow(s,d,f,"bottom","top",C.red);
 const g=node(s,"도착·서비스 시각 반영",350,470,230,70,C.light,C.dark,C.mid);
 const h=node(s,"다음 고객?",80,470,190,64,C.white,C.dark,C.navy);
 arrow(s,e,g,"left","right",C.gold); arrow(s,g,h,"left","right"); arrow(s,h,a,"top","bottom");
 text(s,"arc 진입시각 t의 속도로 통행시간 계산:  cᵢⱼ(t) = dᵢⱼ / vᵢⱼ(t)",650,530,490,42,20,C.navy,true,"center"); footer(s,5); note(s);
}

// 6
{
 const s=deck.slides.add(); title(s,"Re-route는 고객 순서와 기존 차량 간 배정을 조정한다");
 text(s,"세 가지 이웃해를 반복 탐색",72,160,500,30,22,C.gray,true);
 const x1=shape(s,72,215,330,140,C.blueLight,true,C.navy); text(s,"SWAP",95,238,100,28,24,C.navy,true); text(s,"A → B → C\nA → C → B",95,278,250,66,21,C.dark,false);
 const x2=shape(s,475,215,330,140,C.light,true,C.mid); text(s,"RELOCATE",498,238,150,28,24,C.navy,true); text(s,"A → B → C → D\nA → C → D → B",498,278,260,66,21,C.dark,false);
 const x3=shape(s,878,215,330,140,C.goldLight,true,C.gold); text(s,"REINSERT",901,238,150,28,24,C.gold,true); text(s,"T1: A → B → C\nT2: D → B → E",901,278,260,66,21,C.dark,false);
 const a=node(s,"완료 구간 고정",100,460,185,64,C.white,C.dark,C.mid);
 const b=node(s,"이웃해 생성",365,460,185,64,C.white,C.dark,C.mid);
 const c=node(s,"제약 검증",630,460,185,64,C.navy,C.white,C.navy);
 const d=node(s,"더 좋은 해 채택",895,460,210,64,C.gold,C.white,C.gold);
 arrow(s,a,b); arrow(s,b,c); arrow(s,c,d); arrow(s,d,b,"bottom","bottom",C.gold);
 text(s,"개선이 없을 때 종료",930,555,180,24,16,C.gray,true,"center"); footer(s,6); note(s);
}

// 7
{
 const s=deck.slides.add(); title(s,"New truck은 지연 위험 업무를 1…N대 차량에 이전한다");
 const a=node(s,"업무별 지연 위험도",75,190,205,70,C.white,C.dark,C.mid);
 const b=node(s,"이전 가능 업무 정렬",365,190,215,70,C.blueLight,C.navy,C.navy);
 const c=node(s,"k = 1…N 검토",665,190,190,70,C.navy,C.white,C.navy);
 const d=node(s,"차량·위치별 삽입",940,190,215,70,C.goldLight,C.gold,C.gold);
 arrow(s,a,b); arrow(s,b,c); arrow(s,c,d);
 const e=node(s,"전체 경로 재계산",940,365,215,70,C.white,C.dark,C.mid);
 const f=node(s,"용량·시간 검증",665,365,190,70,C.white,C.dark,C.mid);
 const g=node(s,"k별 최적안 저장",365,365,215,70,C.gold,C.white,C.gold);
 const h=node(s,"투입 대수 결정",75,365,205,70,C.navy,C.white,C.navy);
 arrow(s,d,e,"bottom","top"); arrow(s,e,f,"left","right"); arrow(s,f,g,"left","right"); arrow(s,g,h,"left","right");
 shape(s,170,525,940,58,C.light,true,"none"); text(s,"차량은 출발 시 배송 물량을 보유하고 고객 방문 때 적재량이 감소",190,541,900,28,20,C.navy,true,"center");
 footer(s,7); note(s);
}

// 8
{
 const s=deck.slides.add(); title(s,"모든 후보는 실행 가능한 계획인지 먼저 검증한다");
 const labels=[
  ["경로 연결성","모든 고객과 종료 depot까지 통행 가능"],
  ["배송 용량","0 ≤ 현재 적재량 − 누적 배송량 ≤ 차량 용량"],
  ["시간 제약","고객 due time과 최대 운행시간 확인"],
  ["운영 고정","완료 고객·현재 주행 구간·종료 depot 유지"]
 ];
 labels.forEach((v,i)=>{ const y=175+i*112; shape(s,85,y,1110,82,i%2?C.light:C.white,true,i===0?C.navy:C.mid); text(s,String(i+1).padStart(2,"0"),110,y+22,60,30,22,i===0?C.navy:C.gold,true); text(s,v[0],205,y+18,250,32,23,C.dark,true); text(s,v[1],480,y+20,660,30,18,C.gray,false); });
 footer(s,8); note(s);
}

// 9
{
 const s=deck.slides.add(); title(s,"추천은 ‘가장 빠른 안’이 아니라 운영상 균형 잡힌 안이다");
 const cols=[{x:72,t:"시간·서비스",b:"총지연 · 최대지연\n정시율 · 지각 고객",f:C.blueLight,c:C.navy},{x:370,t:"거리·비용",b:"총 이동거리\n운영비 · 신규차량비",f:C.light,c:C.dark},{x:668,t:"운영 변경",b:"순서 변경 수\n업무 재배정 수",f:C.goldLight,c:C.gold},{x:966,t:"실행 가능성",b:"경로 · 용량\n시간 제약",f:"#E5F3ED",c:C.green}];
 cols.forEach(o=>{shape(s,o.x,180,240,160,o.f,true,o.c); text(s,o.t,o.x+18,208,204,30,23,o.c,true,"center"); text(s,o.b,o.x+18,257,204,60,18,C.gray,false,"center");});
 const a=node(s,"Infeasible 제거",100,440,190,64,C.white,C.dark,C.mid);
 const b=node(s,"Pareto frontier",385,440,190,64,C.navy,C.white,C.navy);
 const c=node(s,"ICER / 운영정책",670,440,210,64,C.goldLight,C.gold,C.gold);
 const d=node(s,"추천 + 근거",975,440,190,64,C.gold,C.white,C.gold);
 arrow(s,a,b); arrow(s,b,c); arrow(s,c,d);
 text(s,"추천 결과에는 No-action 대비 지연·거리·비용·변경량을 함께 제시",155,570,970,34,20,C.navy,true,"center"); footer(s,9); note(s);
}

// 10
{
 const s=deck.slides.add(); title(s,"해커톤에서는 설명 가능성과 단계적 완성을 함께 보여준다");
 const steps=[
  ["01","Detour","고객 순서 고정 + 상세 도로 우회","MVP 핵심"],
  ["02","Re-route","Swap · Relocate · 차량 간 Reinsert","운영 최적화"],
  ["03","New truck","k=1…N 투입 대수와 업무 이전","비용–지연 균형"],
  ["04","Recommend","Pareto + 정책 기반 추천 근거","의사결정 지원"]
 ];
 steps.forEach((v,i)=>{const y=165+i*112; text(s,v[0],82,y+18,65,36,26,i===0?C.navy:C.gold,true); shape(s,165,y,1010,78,i===0?C.blueLight:(i===3?C.goldLight:C.light),true,i===0?C.navy:C.mid); text(s,v[1],195,y+18,210,30,23,C.dark,true); text(s,v[2],420,y+19,480,30,18,C.gray,false); text(s,v[3],930,y+19,210,28,17,i===0?C.navy:C.gold,true,"right");});
 text(s,"최종 데모: 교통 변화 → 대안 3개 생성 → KPI 비교 → 추천 이유 설명",105,635,1070,32,22,C.navy,true,"center"); footer(s,10); note(s);
}

await fs.mkdir(PREVIEW,{recursive:true});
for (const [i,s] of deck.slides.items.entries()) {
 const blob=await deck.export({slide:s,format:"png",scale:1});
 await fs.writeFile(`${PREVIEW}/slide-${i+1}.png`,new Uint8Array(await blob.arrayBuffer()));
 const layout=await s.export({format:"layout"});
 await fs.writeFile(`${PREVIEW}/slide-${i+1}.layout.json`,await layout.text());
}
const montage=await deck.export({format:"webp",montage:true,scale:1});
await fs.writeFile(`${PREVIEW}/montage.webp`,new Uint8Array(await montage.arrayBuffer()));
const pptx=await PresentationFile.exportPptx(deck); await pptx.save(OUT);
