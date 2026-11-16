#  민감도 전용 변수를 하나씩·함께 더한다. 결핵 의심 비율 = 같은 흉부 판독 체계의 다른 판정(판독 관행 대리), 단독주택 가구(난방·실내 오염 대리), 내과 전문의 밀도.
#  산출: 04_분석/CHES/results_posthoc/PH_extra_IRR.csv
suppressMessages({library(INLA)}); inla.setOption(num.threads="1:1")
B<-normalizePath(file.path(dirname(sub("--file=","",grep("--file=",commandArgs(),value=TRUE))),"..","04_분석","CHES")); OUT<-file.path(B,"results_posthoc")
DD<-read.csv(file.path(B,"panel_CHES_std3.csv"),check.names=FALSE)
g<-inla.read.graph(file.path(B,"results_std3","nb_CHES.graph"))
RG<-read.csv(file.path(B,"results_std3","S6_spatial_RR.csv"))$fbd_region
stopifnot(length(RG)==g$n); DD$area<-match(DD$fbd_region,RG); stopifnot(!anyNA(DD$area))
DD$time<-DD$year-min(DD$year)+1; DD$yiid<-DD$time
M<-read.csv(file.path(B,"results_std3","S3_main_IRR.csv"))$cov
pc<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)),phi=list(prior="pc",param=c(0.5,2/3)));pcp<-list(prec=list(prior="pc.prec",param=c(0.5,0.01)))
CF<-list(mean=0,prec=4,mean.intercept=0,prec.intercept=0.001)
fit<-function(v,dat=DD){f<-as.formula(paste("cases ~ 1 +",paste(sprintf("`%s`",v),collapse="+"),"+ f(area,model='bym2',graph=g,scale.model=TRUE,constr=TRUE,hyper=pc) + f(time,model='rw1',scale.model=TRUE,hyper=pcp) + f(yiid,model='iid',hyper=pcp)"))
  inla(f,family="nbinomial",data=dat,E=dat$E,control.fixed=CF,control.compute=list(waic=TRUE),control.inla=list(control.vb=list(emergency=50)))}
EX<-list(main=character(0),tb_suspect="ext__tb_suspect_share",detached="detached_house_households",im_spec="im_specialists_per_100k",
         all3=c("ext__tb_suspect_share","detached_house_households","im_specialists_per_100k"))
R<-NULL
EX$drop2123<-character(0)
for(nm in names(EX)){v<-c(M,EX[[nm]]);stopifnot(all(v%in%names(DD)));t0<-Sys.time();m<-if(nm=="drop2123"){d2<-DD[!DD$year%in%2021:2023,];d2$time<-match(d2$year,sort(unique(d2$year)));d2$yiid<-d2$time;fit(v,d2)} else fit(v);s<-m$summary.fixed[-1,]
  r<-data.frame(spec=nm,cov=rownames(s),IRR=round(exp(s$mean),3),lo=round(exp(s$`0.025quant`),3),hi=round(exp(s$`0.975quant`),3),WAIC=round(m$waic$waic,1),
                phi=round(m$summary.hyperpar["Phi for area","mean"],3));r$cov<-gsub("`","",r$cov);r$cred<-r$lo>1|r$hi<1;R<-rbind(R,r)
  cat(sprintf("[88X %s] %-10s WAIC %.1f phi %.3f · %.1f min\n",format(Sys.time(),"%H:%M:%S"),nm,m$waic$waic,r$phi[1],as.numeric(difftime(Sys.time(),t0,units="mins"))))}
write.csv(R,file.path(OUT,"PH_extra_IRR.csv"),row.names=FALSE); cat("done\n")
