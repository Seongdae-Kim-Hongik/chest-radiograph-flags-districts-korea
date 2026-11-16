#!/bin/bash
#  E = 99C2(성×15연령 간접표준화, 판정 수검자 분모, 세종 시도 행 포함 229×14). 풀 = 99c_ches. 비교 결과 RESP·GCA. 민감도 s577·s2·s8, 81 S10 = E_pop.
#  모든 R은 rslot.sh(공유 7슬롯) 경유, nice 10, INLA 1스레드, 5분 부하 14 초과 시 대기.
set -x
S="${ST_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"; cd "$S"; RS="$S/01_스크립트/rslot.sh"; RC="${ST_FBDZIP:?set ST_FBDZIP to the resident population folder}"
export SK_RSLOTS=7
T=CHES; GR="$S/04_분석/$T/graph_593.graph"; D=261116; NW=3; NMV=200
q(){ while [ "$(jobs -rp | wc -l)" -ge 4 ]; do sleep 10; done; }
lw(){ while [ "$(sysctl -n vm.loadavg | awk '{print int($3)}')" -gt 14 ]; do sleep 30; done; }
ST_FBDZIP="$RC" nice -n 10 python3 01_스크립트/99C2_build_Estd3_ches.py || exit 1
nice -n 10 python3 01_스크립트/99c_extra_canonical_pool_ches.py || exit 1
ST_VER=std3 nice -n 10 python3 01_스크립트/80_build_disease_panel_v.py $T > 04_분석/$T/run_80.log 2>&1 || exit 1
python3 ../논문_마스터자료/00_분석전_데이터게이트/data_gate.py 04_분석/$T/panel_${T}_std3.csv --region fbd_region > 04_분석/$T/data_gate_${T}_std3_$D.txt 2>&1
echo "GATE rc=$?"
[ -n "$GATE_ONLY" ] && exit 0
export ST_VER=std3 ST_THREADS=1 ST_GRAPH="$GR"
lw; (cd 01_스크립트 && ST_MV_STOP=1 nice -n 10 $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81a.log 2>&1 || exit 1
echo STAGE_A_done
STEP=$(( (NMV + NW - 1) / NW ))
for k in $(seq 0 $((NW-1))); do a=$(( k*STEP+1 )); b=$(( (k+1)*STEP )); [ $b -gt $NMV ] && b=$NMV; lw; (cd 01_스크립트 && ST_MV_RANGE=$a-$b nice -n 10 $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81_mv_$a.log 2>&1 & sleep 20; done
wait
lw; (cd 01_스크립트 && nice -n 10 $RS Rscript 81_fit_inla.R $T) > 04_분석/$T/run_std3_81b.log 2>&1 || exit 1
python3 01_스크립트/82_core_report.py $T $D > 04_분석/$T/run_std3_82.log 2>&1
python3 01_스크립트/83_check_report.py $T $D >> 04_분석/$T/run_std3_82.log 2>&1
echo "CHAIN done"
( for V in s577 s2 s8; do lw; ST_VER=$V python3 01_스크립트/80_build_disease_panel_v.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") nice -n 10 $RS Rscript 81_fit_inla.R $T); done > 04_분석/$T/run_sens3.log 2>&1 ) &
python3 01_스크립트/87_window_grid.py $T std3; lw; (cd 01_스크립트 && TAG=$T ST_VER=std3 nice -n 10 $RS Rscript 85_window_maps.R $T std3); python3 01_스크립트/86_yearly_maps_ehsa.py $T std3
python3 01_스크립트/88g_sens_prep.py $T std3 RESP,GCA || exit 1
cd 01_스크립트; export TAG=$T NCO=RESP,GCA
L=../04_분석/$T
for G in 1 2 3 4 5 6; do q; lw; GROUP=$G nice -n 10 $RS Rscript 88g_sens_suite.R > $L/run_std3_88g_$G.log 2>&1 & sleep 5; done
q; lw; nice -n 10 $RS Rscript 88h_ppc_varpart.R > $L/run_std3_88h.log 2>&1 &
for G in nb struct kh review; do q; lw; nice -n 10 $RS Rscript 88k_struct_kh.R $G > $L/run_std3_88k_$G.log 2>&1 & sleep 5; done
wait
if grep -q 'KH_typeII FAILED' $L/run_std3_88k_kh.log; then mv $L/results_std3/S43_part_KH_typeII.csv $L/results_std3/S43_part_KH_typeII_failed_init.csv.bak; KH_INIT=0 nice -n 10 $RS Rscript 88k_struct_kh.R kh > $L/run_std3_88k_kh_init0.log 2>&1; fi
cd ..; TAG=$T ST_VER=std3 python3 01_스크립트/89g_sens_combine.py $T std3 > 04_분석/$T/run_std3_89g.log 2>&1
echo "ALL rc=$?"; grep -l "FAILED" 04_분석/$T/run_std3_88*.log; true
