# Re-run generation (previous state was reset).

import re
from pathlib import Path

upper_block = """G30	wieniec dolny i górny	264	282	2	K	0
G30	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G30	półka	264	270	1	K	0
G30	front słoje poziomo	297	716	1	DDKK	0
G30	HDF	280	715	1	0	0
G40	wieniec dolny i górny	364	282	2	D	0
G40	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G40	półka	364	270	1	D	0
G40	front słoje poziomo	397	716	1	DDKK	0
G40	HDF	380	715	1	0	0
G60 P/L	wieniec dolny i górny	564	282	2	D	0
G60 P/L	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60 P/L	półka	564	270	1	D	0
G60 P/L	front słoje poziomo	597	716	1	DDKK	0
G60 P/L	HDF	580	715	1	0	0
G60	wieniec dolny i górny	564	282	2	D	0
G60	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60	półka	564	270	1	D	0
G60	front słoje poziomo	297	716	2	DDKK	0
G60	HDF	580	715	1	0	0
G40G	wieniec dolny i górny	364	412	2	K	0
G40G	boki	720	430	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G40G	półka	364	400	1	K	0
G40G	front słoje poziomo	396	716	1	DDKK	0
G40G	HDF	380	715	1	0	0
G60G	wieniec dolny i górny	564	412	2	D	0
G60G	boki	720	430	2	DKK	pcv 0,8 frez na hdf 412 od przodu gł.12
G60G	półka	564	400	1	D	0
G60G	front słoje poziomo	597	716	1	DDKK	0
G60G	HDF	580	715	1	0	0
N40 nadstawka	wieniec dolny i górny	364	542	2	K	0
N40 nadstawka	boki	360	560	2	KDD	pcv 0,8 frez na hdf 542 od przodu gł.12
N40 nadstawka	front słoje poziomo	397	357	1	DDKK	PCV 2mm
N40 nadstawka	HDF	380	355	1	0	0
N60 nadstawka	wieniec dolny i górny	564	542	2	D	0
N60 nadstawka	boki	360	560	2	KDD	pcv 0,8 frez na hdf 542 od przodu gł.12
N60 nadstawka	front słoje poziomo	597	357	1	DDKK	0
N60 nadstawka	HDF	580	355	1	0	0
G80K	wieniec dolny i górny	764	282	2	D	0
G80K	boki	360	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G80K	front słoje poziomo	797	357	1	DDKK	0
G80K	HDF	780	355	1	0	0
G60K	wieniec dolny i górny	564	282	2	D	0
G60K	boki	360	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60K	front słoje poziomo	597	357	1	DDKK	0
G60K	HDF	580	355	1	0	0
G60N	wieniec dolny i górny	1	1	2	0	0
G60N	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60N	półka	1	1	1	0	0
G60N	listwa 	684	100	1	D	0
G60N	front słoje poziomo	398	716	1	DDKK	0
G60N	HDF	580	715	2	0	0
G80 	wieniec dolny i górny	764	282	2	D	0
G80 	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G80 	półka	764	270	1	D	0
G80 	front słoje poziomo	397	716	2	DDKK	0
G80 	HDF	780	715	1	0	0
G45	wieniec dolny i górny	414	282	2	D	0
G45	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G45	półka	414	270	1	D	0
G45	front słoje poziomo	716	447	1	DDKK	0
G45	HDF	435	715	1	0	0
G80 ociekacz 	wieniec dolny i górny	764	282	2	D	0
G80 ociekacz 	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G80 ociekacz 	front słoje poziomo	397	716	2	DDKK	0
G80 ociekacz 	HDF	780	715	1	0	0
G40K	wieniec dolny i górny	364	282	2	D	0
G40K	boki	360	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G40K	front słoje poziomo	357	397	1	DDKK	0
G40K	HDF	385	355	1	0	0
G45K	wieniec dolny i górny	414	282	2	D	0
G45K	boki	360	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G45K	front słoje poziomo	357	447	1	DDKK	0
G45K	HDF	435	355	1	0	0
N80 nadstawka	wieniec dolny i górny	764	542	2	D	0
N80 nadstawka	boki	360	560	2	KDD	pcv 0,8 frez na hdf 542 od przodu gł.12
N80 nadstawka	front słoje poziomo	357	797	1	DDKK	0
N80 nadstawka	HDF	785	355	1	0	0
N45 nadstawka	wieniec dolny i górny	414	542	2	D	0
N45 nadstawka	boki	360	560	2	KDD	pcv 0,8 frez na hdf 542 od przodu gł.12
N45 nadstawka	front słoje poziomo	357	447	1	DDKK	0
N45 nadstawka	HDF	435	355	1	0	0
G45G	wieniec dolny i górny	414	412	2	K	0
G45G	boki	720	430	2	DKK	pcv 0,8 frez na hdf 412 od przodu gł.12
G45G	półka	414	400	1	K	0
G45G	front słoje poziomo	716	447	1	DDKK	0
G45G	HDF	435	715	1	0	0
G60N WYS.36	wieniec dolny i górny	1	1	2	0	0
G60N WYS.36	boki	360	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60N WYS.36	listwa 	324	100	1	D	0
G60N WYS.36	front słoje poziomo	357	398	1	DDKK	0
G60N WYS.36	HDF	585	715	2	0	0
G60KN/2	wieniec dolny i górny	564	282	2	D	0
G60KN/2	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G60KN/2	półka	564	282	1	D	0
G60KN/2	front słoje poziomo	357	597	2	DDKK	0
G60KN/2	HDF	585	715	1	0	0
G80KN/2	wieniec dolny i górny	764	282	3	D	0
G80KN/2	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G80KN/2	front witryna	357	797	2	DDKK	0
G80KN/2	HDF	780	715	1	0	0
G50	wieniec dolny i górny	464	282	2	D	0
G50	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G50	półka	464	270	1	D	0
G50	front słoje poziomo	716	497	1	DDKK	0
G51	wieniec dolny i górny	474	282	2	D	0
G51	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12
G51	półka	474	270	1	D	0
G51	front słoje poziomo	716	497	1	DDKK	0
GW30P/L	boki	920	320	2	dkk	frez na hdf 282
GW30P/L	wieniec dolny i górny	264	282	2	dkk	0
GW30P/L	listwy	0	0	0	0	0
GW30P/L	front	916	296	1	ddkk	0
GW30P/L	hdf	915	285	1	0	0
GW30P/L	półka	264	270	1	d	0
GW30A P/L	boki	920	320	2	dkk	frez na hdf 282,ramka alu
GW30A P/L	wieniec dolny i górny	264	282	2	d	ramka alu
GW30A P/L	listwy	0	0	0	0	ramka alu
GW30A P/L	front	916	296	1	ddkk	ramka alu
GW30A P/L	hdf	915	285	1	0	ramka alu
GW30A P/L	półka	264	270	1	d	ramka alu
GW40P/L	boki	920	320	2	DKK	frez na hdf 282
GW40P/L	wieniec dolny i górny	364	282	2	dkk	0
GW40P/L	listwy	0	0	0	0	0
GW40P/L	front	916	396	1	ddkk	0
GW40P/L	hdf	915	385	1	0	0
GW40P/L	półka	364	270	1	d	0
GW40A P/L	boki	920	320	2	DKK	frez na hdf 282,ramka alu
GW40A P/L	wieniec dolny i górny	364	282	2	dkk	ramka alu
GW40A P/L	listwy	0	0	0	0	ramka alu
GW40A P/L	front	916	396	1	ddkk	ramka alu
GW40A P/L	hdf	915	385	1	0	ramka alu
GW40A P/L	półka	364	270	1	d	ramka alu
GW45P/L	boki	920	320	2	dkk	frez na hdf 282
GW45P/L	wieniec dolny i górny	414	282	2	dkk	0
GW45P/L	listwy	0	0	0	0	0
GW45P/L	front	916	446	1	ddkk	0
GW45P/L	hdf	915	435	1	0	0
GW45P/L	półka	414	270	1	d	0
GW45AP/L	boki	920	320	2	dkk	frez na hdf 282. ramka alu
GW45P/L	wieniec dolny i górny	414	282	2	dkk	ramka alu
GW45AP/L	listwy	0	0	0	0	ramka alu
GW45AP/L	front	916	446	1	ddkk	ramka alu
GW45AP/L	hdf	915	435	1	0	ramka alu
GW45AP/L	półka	414	270	1	d	ramka alu
GW50P/L	boki	920	320	2	dkk	frez na hdf 282
GW50P/L	wieniec dolny i górny	464	282	2	dkk	0
GW50P/L	listwy	0	0	0	0	0
GW50P/L	front	916	496	1	ddkk	0
GW50P/L	hdf	915	485	1	0	0
GW50P/L	półka	464	270	1	d	0
GW50AP/L	boki	920	320	2	dkk	frez na hdf 282, ramka alu
GW50P/L	wieniec dolny i górny	464	282	2	dkk	ramka alu
GW50AP/L	listwy	0	0	0	0	ramka alu
GW50AP/L	front	916	496	1	ddkk	ramka alu
GW50AP/L	hdf	915	485	1	0	ramka alu
GW50AP/L	półka	464	270	1	d	ramka alu
GW60P/L	boki	920	320	2	dkk	frez na hdf 282
GW60P/L	wieniec dolny i górny	464	282	2	dkk	0
GW60P/L	listwy	0	0	0	0	0
GW60P/L	front	916	496	1	ddkk	0
GW60P/L	hdf	915	585	1	0	0
GW60P/L	półka	564	270	1	d	0
GW60AP/L	boki	920	320	2	dkk	frez na hdf 282, ramka alu
GW60AP/L	wieniec dolny i górny	464	282	2	dkk	ramka alu
GW60AP/L	listwy	0	0	0	0	ramka alu
GW60AP/L	front	916	496	1	ddkk	ramka alu
GW60AP/L	hdf	915	585	1	0	ramka alu
GW60AP/L	półka	564	270	1	d	ramka alu
G30A	wieniec dolny i górny	264	282	2	K	0,RAMKA ALU
G30A	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12,RAMKA ALU 
G30A	półka	264	270	1	K	0, RAMKA ALU
G30A	front słoje poziomo	297	716	1	DDKK	0, RAMKA ALU
G30A	HDF	280	715	1	0	0, RAMKA ALU
G40A	wieniec dolny i górny	364	282	2	D	0, RAMKA ALU
G40A	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12, RAMKA ALU
G40A	półka	364	270	1	D	0, RAMKA ALU
G40A	front słoje poziomo	397	716	1	DDKK	0, RAMKA ALU
G40A	HDF	380	715	1	0	RAMKA ALU
G45A	wieniec dolny i górny	414	282	2	D	 RAMKA ALU
G45A	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12,  RAMKA ALU
G45A	półka	414	270	1	D	RAMKA ALU
G45A	front słoje pion	716	447	1	DDKK	 RAMKA ALU
G45A	HDF	435	715	1	0	RAMKA ALU
G50A	wieniec dolny i górny	464	282	2	D	RAMKA ALU0
G50A	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12,RAMKA ALU 
G50A	półka	464	270	1	D	RAMKA ALU
G50A	front słoje pion	716	497	1	DDKK	RAMKA ALU 
G60A P/L	wieniec dolny i górny	564	282	2	D	RAMKA ALU
G60A P/L	boki	720	300	2	DKK	pcv 0,8 frez na hdf 282 od przodu gł.12, RAMKA ALU
G60A P/L	półka	564	270	1	D	RAMKA ALU
G60A P/L	front słoje pion	597	716	1	DDKK	RAMKA ALU
G60A P/L	HDF	580	715	1	0	RAMKA ALU
"""

lower_block = """D15 cargo	wieniec dolny	114	510	1	D	uwaga
D15 cargo	boki	720	510	2	D	0
D15 cargo	listwy	114	100	2	D	0
D15 cargo	półka	0	0	1	K	0
D15 cargo	front	713	146	1	DDKK	0
D15 cargo	HDF	715	145	1	0	0
D15O	wieniec dolny	114	510	1	D	uwaga
D15O	boki	720	510	2	D	0
D15O	listwy	114	100	2	D	0
D15O	półka	114	500	2	K	0
D15O	HDF	715	145	1	0	0
D20 CARGO	wieniec dolny	164	510	1	KDD	0
D20 CARGO	boki	720	510	2	D	0
D20 CARGO	listwy	164	100	2	D	0
D20 CARGO	front słoje pion	713	196	1	DDKK	0
D20 CARGO	HDF	195	715	1	0	0
D20O	boki	720	510	2	D	0
D20O	wieniec dolny	164	510	1	D	0
D20O	listwy	164	100	2	D	0
D20O	półka	164	500	2	K	0
D30	wieniec dolny	264	510	1	K	0
D30	boki	720	510	2	D	0
D30	listwy	264	100	2	D	0
D30	półka	264	500	1	K	0
D30	front słoje pion	713	296	1	DDKK	0
D30	HDF	295	715	1	0	0
D30O	wieniec dolny	264	510	1	K	0
D30O	boki	720	510	2	D	0
D30O	listwy	264	100	2	D	0
D30O	półka	264	500	1	K	0
D30O	HDF	295	715	1	0	0
D30 CARGO	wieniec dolny	264	510	1	KDD	0
D30 CARGO	boki	720	510	2	D	0
D30 CARGO	listwy	264	100	2	D	0
D30 CARGO	front słoje pion	713	296	1	DDKK	0
D30 CARGO	HDF	295	715	1	0	0
D40 P/L	wieniec dolny	364	510	1	KDD	0
D40 P/L	boki	720	510	2	D	0
D40 P/L	listwy	364	100	2	D	0
D40 P/L	półka	364	500	1	K	0
D40 P/L	front słoje pion	713	396	1	DDKK	0
D40 P/L	HDF	395	715	1	0	0
D40S3	wieniec dolny	364	510	1	KDD	0
D40S3	boki	720	510	2	D	0
D40S3	listwy	364	100	2	D	0
D40S3	front słoje pion	140	396	1	DDKK	0
D40S3	front słoje pion	283	396	2	DDKK	0
D40S3	PŁYTA 18 SPODY	333	448	3	0	0
D40S3	TYŁY 18	333	70	1	D	0
D40S3	TYŁY 18	333	133	2	D	0
D40S3	HDF	395	715	1	0	0
D45	wieniec dolny	414	510	1	KDD	0
D45	boki	720	510	2	D	0
D45	listwy	414	100	2	D	0
D45	półka	414	500	1	K	0
D45	front słoje pion	713	446	1	DDKK	0
D45	HDF	445	715	1	0	0
D60Z	wieniec dolny	564	510	1	DKK	0
D60Z	boki	720	510	2	D	0
D60Z	listwy	564	100	2	D	0
D60Z	front słoje pion	713	596	1	DDKK	0
D60S3	wieniec dolny	564	510	1	DKK	0
D60S3	boki	720	510	2	D	0
D60S3	listwy	564	100	2	D	0
D60S3	front słoje pion	140	140	1	DDKK	0
D60S3	front słoje pion	283	596	2	DDKK	0
D60S3	HDF	595	715	1	0	0
D60S3	PŁYTA 18 SPODY	533	448	3	0	0
D60S3	TYŁY 18	532	70	1	D	0
D60S3	TYŁY 18	532	133	2	D	0
D80S3	wieniec dolny	764	510	1	DKK	0
D80S3	boki	720	510	2	D	0
D80S3	listwy	764	100	2	D	0
D80S3	front słoje pion	140	796	1	DDKK	0
D80S3	front słoje pion	283	796	2	DDKK	0
D80S3	HDF	795	715	1	0	0
D80S3	PŁYTA 18 SPODY	733	448	3	0	0
D80S3	TYŁY 18	732	61	1	D	0
D80S3	TYŁY 18	732	125	2	D	0
Front Zmywarki 60	front słoje pion 60	713	596	1	DDKK	PCV 2mm
Front Zmywarki 45	front słoje pion 45	713	596	1	DDKK	PCV 2mm
D40SP	wieniec dolny	364	510	1	KDD	0
D40SP	boki	2020	560	2	DK	0
D40SP	wieniec górny	364	510	1	K	0
D40SP	przegroda	364	510	1	K	0
D40SP	półki	364	500	4	K	0
D40SP	front słoje pion	713	396	1	DDKK	0
D40SP	front słoje pion	713	396	1	DDKK	0
D40SP	HDF	380	2015	1	0	0
D60ZL	wieniec dolny	564	510	1	DKK	0
D60ZL	boki	2020	560	2	DK	0
D60ZL	wieniec górny	564	510	1	D	0
D60ZL	półka	564	500	1	D	0
D60ZL	front słoje pion	713	596	1	DDKK	0
D60ZL	front słoje pion	1298	596	1	DDKK	0
D60ZL	HDF	580	395	1	0	0
D60R	wieniec dolny	564	510	1	DKK	0
D60R	boki	2020	560	2	DK	0
D60R	wieniec górny	564	510	1	D	0
D60R	przegroda	564	510	1	D	0
D60R	półki	564	500	4	D	0
D60R	front słoje pion	713	596	1	DDKK	0
D60R	front słoje pion	1298	596	1	DDKK	0
D60R	HDF	380	2015	1	0	0
D60 P/L	wieniec dolny	564	510	1	DKK	0
D60 P/L	boki	720	510	2	D	0
D60 P/L	listwy	564	100	2	D	0
D60 P/L	półką	564	500	1	D	0
D60 P/L	front słoje pion	713	596	1	DDKK	0
D60 P/L	HDF	595	715	1	0	0
D60	wieniec dolny	564	510	1	DKK	0
D60	boki	720	510	2	D	0
D60	listwy	564	100	2	D	0
D60	półką	564	500	1	D	0
D60	front słoje pion	713	596	1	DDKK	0
D60	HDF	595	715	1	0	0
D60PM	boki	2020	560	2	DK	0
D60PM	wieniec górny	564	510	1	D	0
D60PM	przegroda	564	510	3	D	0
D60PM	półki	564	500	1	D	0
D60PM	front słoje poziomo	572	596	1	DDKK	0
D60PM	front słoje poziomo	454	596	1	DDKK	0
D60PM	HDF	570	585	1	0	0
D60PM	HDF	455	585	1	0	0
D90N	wieniec dolny	832	832	1	0	0
D90N	boki	720	510	2	D	0
D90N	wieniec górny	832	832	1	0	0
D90N	LISTWA 	684	100	1	D	0
D90N	półki	564	1	1	0	0
D90N	front słoje pion	713	331	1	DDKK	0
D90N	front słoje pion	713	313	1	DDKK	0
D90N	HDF	775	715	2	0	0
D80Z	wieniec dolny	764	510	1	DKK	0
D80Z	boki	720	510	2	D	0
D80Z	listwy	764	100	2	D	0
D80Z	front słoje pion	713	397	2	DDKK	0
D80	wieniec dolny	764	510	1	DKK	0
D80	boki	720	510	2	D	0
D80	listwy	764	100	2	D	0
D80	PÓŁKA	764	500	1	D	0
D80	front słoje pion	713	397	2	DDKK	0
D80	HDF	795	715	1	0	0
D60ZK	wieniec dolny	564	510	1	DKK	0
D60ZK	boki	720	510	2	D	0
D60ZK	listwy	564	100	2	D	0
D60ZK	PÓŁKA	564	510	1	D	0
D60ZK	front słoje pion	110	110	1	DDKK	0
D60P	wieniec dolny	564	510	1	DKK	0
D60P	boki	2020	560	2	DK	0
D60P	wieniec górny	564	510	1	D	0
D60P	przegroda	564	510	2	D	0
D60P	półki	564	500	2	D	0
D60P	front słoje pion	713	596	1	DDKK	0
D60P	front słoje pion	695	596	1	DDKK	0
D60P	HDF	710	585	1	0	0
D60P	HDF	700	585	1	0	0
D60ZK szufladka	wieniec dolny	564	510	1	DKK	0
D60ZK szufladka	boki	720	510	2	D	0
D60ZK szufladka	listwy	564	100	2	D	0
D60ZK szufladka	PÓŁKA	564	510	1	D	0
D60ZK szufladka	boki szuflad	450	60	2	D	0
D60ZK szufladka	elementy szuflad	501	60	2	D	0
D60ZK szufladka	HDF spód szuflady 	445	532	1	0	0
D60ZK szufladka	front słoje pion	110	596	1	DDKK	0
D60P S3	wieniec dolny	564	510	1	DKK	0
D60P S3	boki	2020	560	2	DK	0
D60P S3	wieniec górny	564	510	1	D	0
D60P S3	przegroda	564	510	2	D	0
D60P S3	półki	564	500	1	D	0
D60P S3	front słoje pion	141	596	1	DDKK	0
D60P S3	front słoje pion	284	596	2	DDKK	0
D60P S3	front słoje pion	695	596	1	DDKK	0
D60P S3	PŁYTA 18 SPODY	533	448	3	0	0
D60P S3	TYŁY 18	533	70	1	D	0
D60P S3	TYŁY 18	533	133	2	D	0
D60P S3	HDF	710	580	1	0	0
D60P S3	HDF	310	580	1	0	0
D60PM S2	wieniec dolny	564	510	1	DKK	0
D60PM S2	boki	2020	560	2	DK	0
D60PM S2	wieniec górny	564	510	1	D	0
D60PM S2	przegroda	564	510	3	D	0
D60PM S2	front słoje pion	284	596	2	DDKK	0
D60PM S2	front słoje pion	447	596	1	DDKK	0
D60PM S2	PŁYTA 18 SPODY	533	448	2	0	0
D60PM S2	TYŁY 18	533	125	2	D	0
D60PM S2	HDF	710	580	1	0	0
D60PM S2	HDF	310	580	1	0	0
D40S1	wieniec dolny	364	510	1	KDD	0
D40S1	boki	720	510	2	D	0
D40S1	listwy	364	100	2	D	0
D40S1	pólka	364	500	1	0	0
D40S1	front słoje poziomo	141	396	1	DDKK	0
D40S1	front słoje poziomo	572	396	1	DDKK	0
D40S1	PŁYTA 18 SPODY	333	448	1	0	0
D40S1	TYŁY 18	333	71	1	D	0
D40S1	HDF	395	715	1	0	0
D60S1	wieniec dolny	564	510	1	DKK	0
D60S1	boki	720	510	2	D	0
D60S1	listwy	564	100	2	D	0
D60S1	półka 	564	500	1	D	0
D60S1	front słoje pion	141	596	1	DDKK	0
D60S1	front słoje pion	572	596	1	DDKK	0
D60S1	PŁYTA 18 SPODY	533	448	1	0	0
D60S1	TYŁY 18	533	71	1	D	0
D60S1	HDF	595	715	1	0	0
D80S1	wieniec dolny	764	510	1	DKK	0
D80S1	boki	720	510	2	D	0
D80S1	listwy	764	100	2	D	0
D80S1	pólka 	764	500	1	D	0
D80S1	front słoje pion	141	796	1	DDKK	0
D80S1	front słoje pion	572	397	2	DDKK	0
D80S1	PŁYTA 18 SPODY	733	448	1	0	0
D80S1	TYŁY 18	733	70	1	D	0
D80S1	HDF	595	715	1	0	0
D60S2 comfortbox	wieniec dolny	564	510	1	DKK	0
D60S2 comfortbox	boki	720	510	2	D	0
D60S2 comfortbox	listwy	564	100	2	D	0
D60S2 comfortbox	front słoje pion	357	596	2	DDKK	0
D60S2 comfortbox	PŁYTA 16	489	495	2	0	0
D60S2 comfortbox	TYŁY 16	475	188	2	D	0
D60S2 comfortbox	HDF	595	715	1	0	0
D80S2 comfortbox	wieniec dolny	764	510	1	dkk	0
D80S2 comfortbox	boki	720	510	2	D	0
D80S2 comfortbox	listwy	764	100	2	D	0
D80S2 comfortbox	front słoje pion	357	796	2	DDKK	0
D80S2 comfortbox	PŁYTA 18 SPODY	533	448	2	0	0
D80S2 comfortbox	TYŁY 18	533	188	2	D	0
D80S2 comfortbox	HDF	595	715	1	0	0
D60S1 ZLEW comfortbox	wieniec dolny	564	510	1	KDD	0
D60S1 ZLEW comfortbox	boki	720	510	2	D	0
D60S1 ZLEW comfortbox	listwy	564	100	2	D	0
D60S1 ZLEW comfortbox	front słoje pion	713	596	1	DDKK	0
D60S1 ZLEW comfortbox	PŁYTA 16	489	495	1	0	0
D60S1 ZLEW comfortbox	TYŁY 16	475	188	1	D	0
D60S1 ZLEW comfortbox	HDF	595	715	1	0	0
D80S1 ZLEW comfortbox	wieniec dolny	764	510	1	KDD	0
D80S1 ZLEW comfortbox	boki	720	510	2	D	0
D80S1 ZLEW comfortbox	listwy	764	100	2	D	0
D80S1 ZLEW comfortbox	front słoje pion	713	796	1	DDKK	0
D80S1 ZLEW comfortbox	PŁYTA 16 SPODY	533	448	1	0	0
D80S1 ZLEW comfortbox	TYŁY 16	533	71	1	D	0
D80S1 ZLEW comfortbox	HDF	595	715	1	0	0
DNZ105	wieniec dolny	964	510	1	D	0
DNZ105	boki	720	510	2	D	0
DNZ105	listwy	964	100	2	D	0
DNZ105	półka	964	500	1	D	0
DNZ105	blenda	713	100	1	D	0
DNZ105	blenda tył	720	580	1	D	0
DNZ105	HDF	715	995	1	0	0
DNZ105	front	713	416	1	DDKK	0
DNZ110	boki  	720	510	1	D	0
DNZ110	wieniec 	1014	510	1	D	0
DNZ110	listwy	1014	100	2	D	0
DNZ110	półka	1014	500	1	D	0
DNZ110	front	713	466	1	DDKK	0
DNZ110	blenda	713	100	1	D	0
DNZ110	blenda	720	480	0	0	0
DNZ110	HDF	715	1045	1	D	0
D50	boki	720	510	2	D	0
D50	wieniec dolny	464	510	1	D	0
D50	listwy	464	510	2	D	0
D50	front	713	496	1	DDKK	0
D50	półka	464	500	1	D	0
D50	HDF	715	495	1	0	0
D51	boki	720	510	2	D	0
D51	wieniec dolny	474	510	1	D	0
D51	listwy	474	510	2	D	0
D51	front	713	506	1	DDKK	0
D51	półka	474	500	1	D	0
D51	HDF	715	505	1	0	0
D90 	boki	720	510	2	D	0
D90	wieniec dolny	864	510	1	D	0
D90	listwy	864	100	2	D	0
D90	front	713	446	2	DDKK	0
D90	HDF	715	895	1	0	0
D90S3	boki	720	510	2	D	0
D90S3	wieniec dolny	864	510	1	D	0
D90S3	listwy	864	100	2	D	0
D90S3	fron słoje pion	140	896	1	DDKK	0
D90S3	fron słoje pion	283	896	2	DDKK	0
D90S3	TYŁY 16	775	70	1	D	0
D90S3	TYŁY 17	775	188	2	D	0
D90S3	SPODY 16	789	445	3	0	0
D90S3	HDF	715	895	1	0	0
D60Z P/L	boki	720	510	2	D	0
D60Z P/L	wieniec dolny	564	510	1	D	0
D60Z P/L	listwy	564	100	2	D	0
D60Z P/L	front	713	596	1	DDKK	0
D50Z P/L	boki	720	510	2	D	0
D50Z P/L	wieniec dolny	464	510	1	D	0
D50Z P/L	listwy	464	100	2	D	0
D50Z P/L	front 	713	496	1	DDKK	0
D60Z	boki  	720	510	2	D	0
D60Z	wieniec 	564	510	1	D	0
D60Z	listwy	564	100	2	D	0
D60Z	front	713	297	2	DDKK	0
D60Z	HDF	715	595	1	0	0
"""


def parse(block):
    rows = []
    for line in block.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 7:
            # try collapse multi-spaces
            parts = re.split(r"\s{2,}", line)
        if len(parts) != 7:
            # try regex with numbers
            m = re.match(
                r"^(.*?)\s+(.*?)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*?)\s+(.*)$", line
            )
            if not m:
                continue
            parts = list(m.groups())
        nazwa, part_name, h, w, pcs, wrap, comm = [p.strip() for p in parts]

        def to_int(x):
            try:
                return int(float(x))
            except Exception:
                return 0

        rows.append(
            dict(
                nazwa=nazwa,
                part_name=part_name,
                height_mm=to_int(h),
                width_mm=to_int(w),
                pieces=to_int(pcs),
                wrapping=None if wrap in ("0", "", "NULL", "null") else wrap,
                comments=None if comm in ("0", "", "NULL", "null") else comm,
            )
        )
    return rows


rows = parse(upper_block) + parse(lower_block)


def q(s):
    return s.replace("'", "''")


header = """-- seed_cabinets_option_b.sql
BEGIN;

DROP TABLE IF EXISTS seed_parts_raw;
CREATE TABLE seed_parts_raw (
    nazwa        TEXT NOT NULL,
    part_name    TEXT NOT NULL,
    height_mm    INTEGER NOT NULL,
    width_mm     INTEGER NOT NULL,
    pieces       INTEGER NOT NULL,
    wrapping     TEXT NULL,
    comments     TEXT NULL
);
"""

insert_sql = []
for r in rows:
    wrapping_val = "NULL" if r["wrapping"] is None else f"'{q(r['wrapping'])}'"
    comments_val = "NULL" if r["comments"] is None else f"'{q(r['comments'])}'"
    insert_sql.append(
        "INSERT INTO seed_parts_raw (nazwa, part_name, height_mm, width_mm, pieces, wrapping, comments) VALUES "
        f"('{q(r['nazwa'])}', '{q(r['part_name'])}', {r['height_mm']}, {r['width_mm']}, {r['pieces']}, "
        f"{wrapping_val}, {comments_val});"
    )

transform = """
INSERT INTO cabinet_types (kitchen_type, name, created_at, updated_at)
SELECT DISTINCT 'LOFT', s.nazwa, NOW(), NOW()
FROM seed_parts_raw s
WHERE NOT EXISTS (SELECT 1 FROM cabinet_types ct WHERE ct.name = s.nazwa);

WITH src AS (
    SELECT
        ct.id AS cabinet_type_id,
        s.part_name,
        s.height_mm,
        s.width_mm,
        s.pieces,
        NULLIF(s.wrapping, '') AS wrapping,
        s.comments,
        CASE
            WHEN LOWER(s.part_name) LIKE '%hdf%' THEN 'HDF'
            WHEN LOWER(s.part_name) LIKE '%front%' THEN 'FRONT'
            WHEN s.part_name ILIKE '%PŁYTA 16%' OR s.part_name ILIKE '%TYŁY 16%' OR s.part_name ILIKE '%SPODY 16%' THEN 'PLYTA'
            WHEN s.part_name ILIKE '%PŁYTA 18%' OR s.part_name ILIKE '%TYŁY 18%' OR s.part_name ILIKE '%SPODY 18%' THEN 'PLYTA'
            ELSE 'PLYTA'
        END AS material,
        CASE
            WHEN LOWER(s.part_name) LIKE '%hdf%' THEN 3
            WHEN s.part_name ILIKE '%PŁYTA 16%' OR s.part_name ILIKE '%TYŁY 16%' OR s.part_name ILIKE '%SPODY 16%' THEN 16
            WHEN s.part_name ILIKE '%PŁYTA 18%' OR s.part_name ILIKE '%TYŁY 18%' OR s.part_name ILIKE '%SPODY 18%' THEN 18
            WHEN LOWER(s.part_name) ~ '^(boki|wieniec|listwy|półka|polka|spody|tyły|tyly)\\b' THEN 18
            ELSE NULL
        END AS thickness_mm,
        CASE WHEN s.comments IS NOT NULL THEN jsonb_build_object('note', s.comments) ELSE NULL END AS processing_json
    FROM seed_parts_raw s
    JOIN cabinet_types ct ON ct.name = s.nazwa
)
INSERT INTO cabinet_parts
    (cabinet_type_id, part_name, height_mm, width_mm, pieces, wrapping, comments, material, thickness_mm, processing_json, created_at, updated_at)
SELECT cabinet_type_id, part_name, height_mm, width_mm, pieces, wrapping, comments, material, thickness_mm, processing_json, NOW(), NOW()
FROM src
WHERE NOT EXISTS (
    SELECT 1 FROM cabinet_parts p
    WHERE p.cabinet_type_id = src.cabinet_type_id
      AND p.part_name       = src.part_name
      AND p.height_mm       = src.height_mm
      AND p.width_mm        = src.width_mm
      AND p.pieces          = src.pieces
      AND COALESCE(p.wrapping,'') = COALESCE(src.wrapping,'')
      AND COALESCE(p.comments,'') = COALESCE(src.comments,'')
);

COMMIT;
"""

sql = header + "\n".join(insert_sql) + "\n" + transform

path = Path(__file__).with_name("seed_cabinets_option_b.sql")
with path.open("w", encoding="utf-8") as f:
    f.write(sql)

(len(rows), path)
