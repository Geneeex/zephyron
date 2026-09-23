from pathlib import Path
import os,sys,csv,json,math,argparse
BASE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='Render nine analytical scenario figures.')
parser.add_argument('--data',type=Path,default=BASE/'analysis')
parser.add_argument('--output',type=Path,default=BASE.parent/'build/reproduced/figures')
args=parser.parse_args()
os.environ.setdefault('MPLCONFIGDIR',str(BASE.parent/'build/matplotlib-cache'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.ticker import AutoLocator, MaxNLocator, NullFormatter
DATA=args.data.resolve();OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
TEAL='#087E8B';AMBER='#D18A17';BLACK='#17242B';GRAY='#73838A'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,'axes.titlesize':10,'axes.titleweight':'bold','axes.edgecolor':BLACK,'axes.labelcolor':BLACK,'text.color':BLACK,'xtick.color':BLACK,'ytick.color':BLACK,'axes.spines.top':False,'axes.spines.right':False,'grid.color':'#DEE5E7','grid.linewidth':.6,'axes.grid':True,'axes.axisbelow':True,'lines.linewidth':1.8,'legend.fontsize':8,'legend.frameon':False,'svg.fonttype':'none','savefig.facecolor':'white'})
captions=[]
inputs=json.loads((DATA/'analysis_provenance.json').read_text(encoding='utf-8'))
B=inputs['baseline_snapshot'];S=inputs['scenario_registry_snapshot'];P=inputs['derived_parameters']
M=S['component_specs']['motor'];A=B['arm'];GEO=B['geometry_mm'];OP=B['operating_assumptions']
CAP=dict(energy=P['energy_Wh'],usable_fraction=100*OP['usable_battery_fraction'],aux=P['auxiliary_W'],drive=P['drive_W'],pv_derating=P['pv_derating'],pv=P['pv_W'],mass=P['mass_kg'],diameter=GEO['wheel_diameter'],rolling=P['rolling'],motor_voltage=M['nominal_voltage_V'],grade=OP['modeled_grade_deg'],rpm=M['free_speed_rpm'],track=GEO['track_center_to_center'],L1mm=A['upper_link_m']*1000,L2mm=A['forearm_m']*1000,m1=A['upper_link_mass_kg_assumed'],m2=A['forearm_mass_kg_assumed'],mh=A['hand_mass_kg_assumed'],arm_factor=A['dynamic_design_factor_assumed'],adc_bits=S['tds']['ADC_bits_assumed'],adc_V=S['tds']['ADC_reference_V_assumed'],uT=S['tds']['temperature_standard_uncertainty_C_assumed'])
def read(name):
 with (DATA/name).open() as f:return list(csv.DictReader(f))
def vals(rows,key):return np.array([float(r[key]) for r in rows])
def layout(title,n=2,height=4.5):
 fig,ax=plt.subplots(n,1,figsize=(6.5,height),squeeze=False)
 fig.suptitle(title,x=.14,ha='left',y=.975,fontsize=11.6,fontweight='bold')
 fig.text(.14,.915,'ANALYTICAL SCENARIOS  /  NO EXPERIMENTAL DATA',fontsize=8,color=GRAY)
 fig.subplots_adjust(left=.14,right=.97,bottom=.13,top=.815,hspace=.82)
 return fig,list(ax[:,0])

def save(fig,stem,title,caption,data,sources):
 # Assumptions remain in the complete caption; retain the visible scenario flag.
 for artist in list(fig.texts):
  if artist is fig._suptitle:continue
  if artist.get_text().startswith('ANALYTICAL SCENARIOS'):
   artist.set_fontsize(8)
  else:artist.remove()
 for ax in fig.axes:
  ax.tick_params(axis='both',which='major',labelsize=8.3,pad=2.5)
  ax.xaxis.label.set_fontsize(9);ax.yaxis.label.set_fontsize(9)
  ax.title.set_fontsize(9.4)
  ax.title.set_position((.5,1.01))
  if ax.get_xscale()=='linear' and isinstance(ax.xaxis.get_major_locator(),AutoLocator):
   ax.xaxis.set_major_locator(MaxNLocator(nbins=5,steps=[1,2,2.5,5,10]))
  if ax.get_yscale()=='linear' and isinstance(ax.yaxis.get_major_locator(),AutoLocator):
   ax.yaxis.set_major_locator(MaxNLocator(nbins=4,steps=[1,2,2.5,5,10]))
  if ax.get_xscale()=='log':ax.xaxis.set_minor_formatter(NullFormatter())
  if ax.get_yscale()=='log':ax.yaxis.set_minor_formatter(NullFormatter())
  legend=ax.get_legend()
  if legend:
   for text in legend.get_texts():text.set_fontsize(8.3)
 for legend in fig.legends:
  for text in legend.get_texts():text.set_fontsize(8.3)
 fig.canvas.draw()
 visible_axis_fonts=[t.get_fontsize() for ax in fig.axes for t in ([ax.xaxis.label,ax.yaxis.label]+ax.get_xticklabels()+ax.get_yticklabels()) if t.get_visible() and t.get_text()]
 legend_fonts=[t.get_fontsize() for ax in fig.axes if ax.get_legend() for t in ax.get_legend().get_texts()]+[t.get_fontsize() for legend in fig.legends for t in legend.get_texts()]
 assert min(visible_axis_fonts+legend_fonts)>=8,(stem,visible_axis_fonts,legend_fonts)
 assert 4.0<=fig.get_size_inches()[1]<=4.6
 fig.savefig(OUT/(stem+'.svg'))
 fig.savefig(OUT/(stem+'.png'),dpi=300)
 captions.append(dict(id=stem,title=title,caption=caption,data_files=data,source_keys=sources,evidence_status='CALCULATED_OR_MODELLED_NOT_OBSERVED',svg=stem+'.svg',png=stem+'.png',width_inches=6.5,height_inches=float(fig.get_size_inches()[1]),minimum_axis_legend_font_pt=8.3,dpi=300))
 plt.close(fig)
# 1 energy
fig,axs=layout('Mission endurance depends on drive duty')
rows=read('energy_duty_sweep.csv')
for G,col,ls in [(0,BLACK,'-'),(500,TEAL,'-'),(1000,AMBER,'--')]:
 rr=[r for r in rows if int(r['irradiance_W_m2'])==G and r['runtime_h']]
 axs[0].plot(vals(rr,'drive_duty_fraction')*100,vals(rr,'runtime_h'),label=f'{G} W/m²',color=col,ls=ls)
axs[0].set(xlim=(0,100),ylim=(0,12),xlabel='Drive duty (%)',ylabel='Depletion time (h)',title='a  Constant-condition energy balance')
fig.legend(*axs[0].get_legend_handles_labels(),loc='center',bbox_to_anchor=(.56,.884),ncol=3,fontsize=8.3,columnspacing=1.4,handlelength=2);axs[0].axhline(6,color=GRAY,ls=':',lw=1)
axs[0].annotate('6 h reference',xy=(97,6),xytext=(97,6.3),ha='right',fontsize=8,color=GRAY)
rr=read('energy_mission_duty_limits.csv')
for G,col,ls in [(0,BLACK,'-'),(500,TEAL,'-'),(1000,AMBER,'--')]:
 r=[x for x in rr if int(x['irradiance_W_m2'])==G and float(x['mission_h']) in S['energy']['plotted_mission_hours'] and x['max_drive_duty_fraction']!=''];axs[1].plot(vals(r,'mission_h'),vals(r,'max_drive_duty_fraction')*100,color=col,ls=ls,marker='o',ms=4,label=f'{G} W/m²')
axs[1].set(ylim=(0,100),xticks=(2,4,6,8),xlabel='Mission duration (h)',ylabel='Maximum drive\nduty (%)',title='b  Feasible duty under the selected budget')
fig.text(.13,.035,'72 Wh label basis · 80% usable · 5 W auxiliary + 35 W during motion · PV derating 0.75',fontsize=7.2)
save(fig,'ENG_F01_energy_duty','Energy-limited mission duration','Analytical scenario; no experimental data. The 72 Wh label-based energy,80%usable fraction,5Wauxiliary demand,35Wbattery-side driving increment,and0.75PVderating define this calculation. Irradiance is constant,not a weather forecast. Top panel is displayed only to12h; missing low-duty branches under sunlight correspond to nonpositive net battery demand,not validated unlimited endurance. Bottom panel inverts the same balance for maximum drive duty. Arm,lighting,and pump loads require additional budgets.',['energy_duty_sweep.csv','energy_mission_duty_limits.csv'],['ENG_BATTERY','ENG_PANEL','ENG_PVWATTS'])
# 2 solar
fig,axs=layout('Solar input and recharge are conditional')
r=read('pv_irradiance_temperature.csv')
for T,col,ls in [(25,BLACK,'-'),(40,GRAY,'--'),(50,TEAL,'-'),(60,AMBER,'--')]:
 rr=[x for x in r if int(x['cell_temperature_C'])==T];axs[0].plot(vals(rr,'irradiance_W_m2'),vals(rr,'panel_dc_W'),color=col,ls=ls,label=f'Cell {T} °C')
axs[0].set(xlim=(0,1000),ylim=(0,21),xlabel='Plane-of-array irradiance (W/m²)',ylabel='Panel DC power (W)',title='a  Nameplate scaling and temperature sensitivity');axs[0].legend(ncol=2)
r=read('solar_recharge_lower_bound.csv');axs[1].plot(vals(r,'irradiance_W_m2'),vals(r,'recharge_label_energy_h'),'-o',color=TEAL,ms=4)
axs[1].set(ylim=(0,26),xlabel='Constant irradiance (W/m²)',ylabel='Recharge lower\nbound (h)',title='b  Empty-to-full energy replacement, load disabled')
axs[1].annotate(f"{P['energy_Wh']/(P['pv_W']*P['pv_derating']):g} h energy-only bound",xy=(1000,P['energy_Wh']/(P['pv_W']*P['pv_derating'])),xytext=(620,10),arrowprops=dict(arrowstyle='-',color=GRAY),fontsize=8)
fig.text(.13,.035,'20 W panel · temperature coefficient −0.38%/K · recharge panel uses combined 0.75 derating',fontsize=7.2)
save(fig,'ENG_F02_solar','Solar power sensitivity and recharge lower bound','Analytical scenario; no experimental data. The upper panel applies the selectedNewpowa20Wmodule temperature coefficient to plane-of-array irradiance without the lumped mission derating. The lower panel separately uses0.75combined derating and72Wh replacement with rover load disabled. Temperature losses must not be double-counted between panels. Constantirradiance,unchangingorientation,and ideal energy accounting omit charge taper,weather,shading,storage losses,and controller headroom; plotted recharge times are lowerbounds.',['pv_irradiance_temperature.csv','solar_recharge_lower_bound.csv'],['ENG_PANEL','ENG_BATTERY','ENG_BQ24650'])
# 3 grade
fig,axs=layout('Initial traction and motor sizing')
r=read('grade_load.csv');x=vals(r,'grade_deg')
axs[0].plot(x,vals(r,'torque_each_Nm'),color=TEAL,label='Equal-share wheel torque')
axs[0].axhline(P['gearbox_Nm'],color=AMBER,ls='--',label=f"Gearbox recommendation: {P['gearbox_Nm']:.3f} N·m")
axs[0].axvline(OP['modeled_grade_deg'],color=GRAY,ls=':',lw=1);axs[0].set(xlim=(0,20),ylim=(0,1.1),xlabel='Grade (°)',ylabel='Torque per wheel (N·m)',title='a  Steady grade demand');axs[0].text(19.5,1.015,f"Gearbox guide: {P['gearbox_Nm']:.3f} N·m",ha='right',fontsize=8.3,color=AMBER)
axs[1].plot(x,vals(r,'approx_current_each_A'),color=TEAL,label='Linear current estimate')
axs[1].axhline(P['current_guidance_A'],color=AMBER,ls='--',label=f"{100*M['continuous_current_fraction_of_stall']:g}% of extrapolated stall current")
axs[1].axvline(OP['modeled_grade_deg'],color=GRAY,ls=':',lw=1);axs[1].set(xlim=(0,20),ylim=(0,2),xlabel='Grade (°)',ylabel='Current per motor (A)',title='b  Linear motor-current estimate');axs[1].text(.5,1.47,f"{100*M['continuous_current_fraction_of_stall']:g}% of stall-current guide",ha='left',fontsize=8.3,color=AMBER)
fig.text(.13,.035,'12 kg gross target · 165 mm wheels · rolling coefficient 0.04 assumed · no turning or sinkage',fontsize=7.2)
save(fig,'ENG_F03_grade_motor','Steady slope and motor sizing','Analytical scenario; no experimental data. Equal wheel loading,12kggrossmass,165mmwheel diameter,androlling-resistancecoefficient0.04are assumed. Torque followsmg(sinθ+Crrcosθ)r/4;current is a linear interpolation usingPololu4755free-running and extrapolatedstall values at12V. Dashed horizontal lines show manufacturer design recommendations,not validated rover safety limits. The10°line marks a proposedtestcondition. Acceleration,skidturning,obstacleimpacts,sinkage,motorheating,and PWMconversion are excluded.',['grade_load.csv'],['ENG_MOTOR','ENG_SKID'])
# 4 kinematics
fig,axs=layout('Wheel geometry influences speed and heading')
r=read('wheel_diameter_speed.csv');axs[0].plot(vals(r,'diameter_mm'),vals(r,'no_load_speed_m_s'),color=TEAL)
axs[0].axvline(GEO['wheel_diameter'],color=AMBER,ls='--',label=f"Selected diameter {GEO['wheel_diameter']:g} mm");axs[0].set(xlabel='Wheel diameter (mm)',ylabel='No-load speed (m/s)',title=f"a  Kinematic ceiling at {M['free_speed_rpm']:g} rpm");axs[0].legend()
r=read('odometry_mismatch_paths.csv')
for eps,col,ls in [(0,BLACK,':'),(.005,GRAY,'--'),(.01,TEAL,'-'),(.02,AMBER,'-')]:
 rr=[z for z in r if float(z['diameter_mismatch_fraction'])==eps];axs[1].plot(vals(rr,'forward_m'),vals(rr,'lateral_error_m'),color=col,ls=ls,label=f'{eps*100:g}% mismatch')
axs[1].set(xlim=(0,10),ylim=(-.05,2),xlabel='Forward displacement (m)',ylabel='Lateral deviation (m)',title='b  Ideal equal-speed command with unequal wheel radii');axs[1].legend(ncol=2)
fig.text(.13,.035,'538 mm effective track assumed · ideal differential-drive equations · ground slip omitted',fontsize=7.2)
save(fig,'ENG_F04_kinematic_sensitivity','Wheel diameter and systematic steering sensitivity','Analytical scenario; no experimental data. The upper panel usesv=πDn/60and100rpmfree-running motor speed,not ground speed underload. The lower panel assumes equal wheel angular speeds,538mmeffective track,and right-to-left rolling-radius mismatches of0–2%. Paths end at10mcenterline path length. Full four-wheel skidturning and actively steered knuckle motion require a different or experimentally identified model. Diameter variation is a sensitivity study,not a measurement of the photographed tires.',['wheel_diameter_speed.csv','odometry_mismatch_paths.csv'],['ENG_MOTOR','ENG_ODOM','ENG_SKID'])
# 5 arm
fig=plt.figure(figsize=(6.5,4.4));gs=fig.add_gridspec(1,2,width_ratios=[1,1.08]);ax0=fig.add_subplot(gs[0]);ax1=fig.add_subplot(gs[1]);fig.suptitle('Manipulator reach and gravitational demand',x=.10,ha='left',y=.975,fontsize=11.6,fontweight='bold');fig.text(.10,.915,'ANALYTICAL SCENARIOS  /  NO EXPERIMENTAL DATA',fontsize=8,color=GRAY);fig.subplots_adjust(left=.10,right=.98,bottom=.23,top=.78,wspace=.62)
L1=A['upper_link_m'];L2=A['forearm_m']
workspace=read('arm_unconstrained_workspace.csv')
outer=[(float(z['forward_m']),float(z['vertical_m'])) for z in workspace if z['boundary']=='outer']
inner=[(float(z['forward_m']),float(z['vertical_m'])) for z in workspace if z['boundary']=='inner']
ax0.add_patch(Polygon(outer,closed=True,facecolor=TEAL,alpha=.10,edgecolor=TEAL));ax0.add_patch(Polygon(inner,closed=True,facecolor='white',edgecolor=GRAY,ls='--'));ax0.plot([0,L1,L1+L2],[0,0,0],'-o',color=BLACK,ms=4);ax0.text(.075,.027,'L₁',ha='center',fontsize=8);ax0.text(.285,.027,'L₂',ha='center',fontsize=8)
ax0.set(aspect='equal',xlim=(-.45,.45),ylim=(-.45,.45),xlabel='Forward offset (m)',ylabel='Vertical offset (m)',title='a  Ideal reach from shoulder')
ax0.set_anchor('N');ax0.text(-.40,.33,f'rₘₐₓ = {L1+L2:.3f} m\nrₘᵢₙ = {abs(L2-L1):.3f} m',fontsize=8)
r=read('arm_torque_budget.csv');xp=vals(r,'grasp_payload_scenario_kg')
for key,col,ls,label in [('shoulder_gravity_torque_Nm',TEAL,'-','Shoulder gravity'),('elbow_gravity_torque_Nm',GRAY,'-','Elbow gravity'),('shoulder_with_design_allowance_Nm',AMBER,'--',f"Shoulder ×{A['dynamic_design_factor_assumed']:g} allowance")]:ax1.plot(xp,vals(r,key),color=col,ls=ls,label=label)
ax1.axvspan(*S['arm']['plotted_payload_band_kg'],color=TEAL,alpha=.06);ax1.set(xlim=(0,.3),ylim=(0,5),xlabel='Grasped mass (kg)',ylabel='Joint torque (N·m)',title='b  Horizontal-arm demand');fig.legend(*ax1.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.5,.035),ncol=3,fontsize=8.3,columnspacing=1.3,handlelength=2)
fig.text(.13,.025,'L₁ = 0.146 m · L₂ = 0.264 m · link masses 0.12/0.16 kg + 0.13 kg hand assumed',fontsize=7.2)
save(fig,'ENG_F05_arm','Arm workspace envelope and torque budget','Analytical scenario; no experimental data or payloadrating. The reach annulus is the ideal unconstrained two-link locus from|L2−L1|toL1+L2with selected146mmand264mmlinks. It ignores jointlimits,chassis/floorcollisions,cables,and gripperlength. Horizontal-arm torque uses allocatedlinkmasses0.12/0.16kgandhandmass0.13kg. The0.15–0.25kgshadedband is a payloadscenario,not demonstrated capacity. Factor2is a stateddesign allowance,not validation of dynamic loads or thermalactuatorcapability.',['arm_torque_budget.csv','arm_unconstrained_workspace.csv','baseline_parameters.csv'],[])
#6 GM
fig,axs=layout('Counting precision requires integration time')
r=read('gm_counting_time.csv')
for rate,col,ls in [(.2,AMBER,'--'),(1,TEAL,'-'),(5,BLACK,'-'),(20,GRAY,':')]:
 rr=[z for z in r if float(z['rate_counts_s'])==rate];axs[0].loglog(vals(rr,'integration_s'),100*vals(rr,'relative_poisson_standard_uncertainty'),color=col,ls=ls,label=f'{rate:g} counts/s')
axs[0].axhline(10,color=GRAY,ls=':',lw=1);axs[0].set(xlabel='Integration time (s)',ylabel='Relative standard\nuncertainty (%)',title='a  Ideal Poisson counting, background omitted');axs[0].legend(ncol=2)
r=read('gm_background_scenario.csv')
for tb,col,ls in [(60,AMBER,'--'),(300,TEAL,'-')]:
 rr=[z for z in r if float(z['signal_rate_cps'])==1 and float(z['background_rate_cps'])==1 and float(z['background_duration_s'])==tb];axs[1].plot(vals(rr,'sample_duration_s'),100*vals(rr,'net_relative_standard_uncertainty'),color=col,ls=ls,marker='o',ms=3,label=f'Background window {tb} s')
axs[1].set(xlabel='Sample integration time (s)',ylabel='Net relative\nuncertainty (%)',title='b  Background subtraction: 1 count/s net signal');axs[1].legend()
fig.text(.13,.035,'Expected counts, not simulated observations · independent Poisson model · no dose conversion',fontsize=7.2)
save(fig,'ENG_F06_gm_uncertainty','Count integration and background uncertainty','Analytical scenario; no experimental radiationdata. Panelashows1/√(λt)forassumedconstantcountingrates,with idealPoisson events andno deadtime. Panelbassumes1count/snetsignaland1count/sbackground;sampleandbackgroundcountwindows are independent. Calibration,energyresponse,deadtime,and temporalbackgrounddrift are excluded. Relativeuncertainty canexceed100%whenfew expectedcounts are available. Theseplots determine candidateintegrationtimes,not a dose-ratecapability or safetyclassification.',['gm_counting_time.csv','gm_background_scenario.csv'],['ENG_IAEA_STATS','ENG_IAEA_GM'])
#7 tds
fig,axs=layout('TDS limits and a partial uncertainty budget')
r=read('tds_fullscale_spec.csv');axs[0].plot(vals(r,'indicated_ppm'),vals(r,'equivalent_relative_limit_pct'),'-o',color=TEAL,ms=3)
axs[0].axhline(10,color=AMBER,ls='--',label='10% of reading (different specification)');axs[0].set(xlim=(0,1020),ylim=(0,210),xlabel='Indicated TDS (ppm)',ylabel='Relative limit (%)',title='a  ±100 ppm expressed relative to the indication');axs[0].legend()
r=read('tds_partial_uncertainty.csv');x=np.arange(len(r));w=.25
for offset,key,col,label in [(-w,'ADC_quantization_standard_uncertainty_ppm',GRAY,'ADC quantization'),(0,'temperature_contribution_ppm',TEAL,'Temperature'),(w,'combined_partial_uncertainty_ppm',AMBER,'RSS combined')]:axs[1].bar(x+offset,vals(r,key),width=w*.92,color=col,label=label)
axs[1].set(xticks=x,xticklabels=[f'{float(z["voltage_V"]):g}' for z in r],xlabel='Sensor voltage at 25 °C (V)',ylabel='Standard\nuncertainty (ppm)',title='b  Two contributions only; calibration is excluded');axs[1].legend(ncol=3,fontsize=8.3,loc='upper left');axs[1].set_ylim(0,1.42*max(vals(r,'combined_partial_uncertainty_ppm')))
fig.text(.13,.035,'Vendor full-scale limit ≠ standard uncertainty · 5 V, 10-bit ADC · u(T) = 0.5 °C assumed',fontsize=7.2)
save(fig,'ENG_F07_tds','Full-scale TDS specification and partial uncertainty','Calculated specification interpretation and analyticalscenario; noexperimentaldata. TheSEN0244manufacturer limit is±10%of1000ppmfullscale,equivalent to±100ppm;panelashows its relative size across readings. It is not a probabilistic uncertainty or accuracy demonstrated ontherover. Panelbpropagates10-bit5VADCquantization and assumedtemperaturestandarduncertainty0.5°Cthrough thevendor conversion. Calibration,matrixeffects,drift,referencevoltage,fouling,and covariance are absent,so RSSvaluesare onlyapartialbudget.',['tds_fullscale_spec.csv','tds_partial_uncertainty.csv'],['ENG_TDS','ENG_TDS_CODE','ENG_GUM'])
#8 detection confidence
fig,axs=layout('Zero misses still leave statistical uncertainty',n=1,height=4.0);ax=axs[0]
fig.texts[1].set_y(.90)
fig.subplots_adjust(top=.80)
confidence_rows=read('zero_miss_confidence.csv');n=vals(confidence_rows,'independent_positive_trials');p=100*vals(confidence_rows,'upper_miss_probability');ax.plot(n,p,color=TEAL);ax.axhline(5,color=AMBER,ls='--',label='5% miss-probability reference');ax.axvline(59,color=GRAY,ls=':',label='59 independent zero-miss trials')
for ni in S['confidence']['annotation_trials']:
 pi=100*float(next(z['upper_miss_probability'] for z in confidence_rows if int(z['independent_positive_trials'])==ni));ax.plot(ni,pi,'o',color=BLACK,ms=4);ax.annotate(f'n={ni}: {pi:.2f}%',(ni,pi),xytext=(8,10),textcoords='offset points',fontsize=8)
ax.set(xlim=(0,200),ylim=(0,60),xlabel='Independent positive trials with zero misses (n)',ylabel='95% upper miss-probability\nbound (%)');ax.legend(loc='upper right',fontsize=7.5)
fig.subplots_adjust(bottom=.17);fig.text(.13,.04,'Exact one-sided binomial calculation · pᵤ = 1 − 0.05¹⁄ⁿ · no trials have been performed',fontsize=7.2)
save(fig,'ENG_F08_detection_confidence','Detection trial count and uncertainty','Analytical sample-size calculation; noexperimentaltrials. Withzeroobservedmisses in nindependentpositiveBernoullitrials,theexactone-sided95%uppermiss-probabilitybound is1−0.05^(1/n). Atleast59zero-misstrials are neededtoboundthemissprobabilitybelow5%forthetestedconditiondistribution. Thecalculationdoesnot establish MQ-2selectivity,modelaccuracy,or generalfieldreliability. Repeatedframesorreadingsfromasingleexposuremustnotbetreatedasindependenttrials.',['zero_miss_confidence.csv'],['ENG_BINOM'])
#9 latency
fig,axs=layout('Vision timing is an end-to-end property',height=4.6)
fig.subplots_adjust(bottom=.16,top=.82,hspace=.89)
r=read('vision_latency_scenarios.csv')
for link,col,ls in [(1,AMBER,'--'),(2,TEAL,'-'),(5,BLACK,'-'),(10,GRAY,':')]:
 rr=[z for z in r if int(z['capture_fps'])==5 and int(z['link_Mbps'])==link];axs[0].plot(vals(rr,'inference_ms'),vals(rr,'total_event_to_display_ms'),color=col,ls=ls,marker='o',ms=3,label=f'{link} Mbit/s')
axs[0].set(xlabel='Inference time (ms)',ylabel='Conditional delay (ms)',title='a  Acquisition at 5 FPS, 40 kB frames');fig.legend(*axs[0].get_legend_handles_labels(),loc='center',bbox_to_anchor=(.565,.884),ncol=4,fontsize=8.3,columnspacing=1.25,handlelength=1.8)
config=[(5,2,50),(20,2,50),(20,10,50),(20,10,25)];labels=['5 FPS\n2 Mbit/s\n50 ms infer','20 FPS\n2 Mbit/s\n50 ms infer','20 FPS\n10 Mbit/s\n50 ms infer','20 FPS\n10 Mbit/s\n25 ms infer'];bottom=np.zeros(4)
components=[('acquisition_wait_mean_ms',GRAY,'Acquisition wait'),('transfer_ms',TEAL,'Transfer'),('inference_ms',AMBER,'Inference'),('other_pipeline_ms',BLACK,'Other pipeline')]
rr=[[z for z in r if (int(z['capture_fps']),int(z['link_Mbps']),int(z['inference_ms']))==c][0] for c in config]
for key,col,label in components:
 y=vals(rr,key);axs[1].bar(np.arange(4),y,bottom=bottom,color=col,width=.58,label=label);bottom+=y
axs[1].set(xticks=np.arange(4),xticklabels=labels,ylabel='Conditional delay (ms)',title='b  Component contributions for four scenarios');axs[1].legend(ncol=4,fontsize=8.3,loc='upper right',columnspacing=1.1,handlelength=1.7);axs[1].set_ylim(0,500)
fig.text(.13,.023,'Queueing, jitter, loss and braking omitted · remote edge inference · selected values, not measured timing',fontsize=7.1)
save(fig,'ENG_F09_vision_latency','Vision pipeline latency scenarios','Analytical scenario; nohardwaretimingdata. Acquisitionwait is1/(2fc),networktransferis8S/RwithS=40000bytes,anddecode/postprocessing/displaytotal50ms. Allrates,timings,andJPEGsizes are assumed. Queueing,retransmission,jitter,andmodelmisses areexcluded. Upperpanelholds5FPS;lowerpanelshowscomponentcontributions. At0.35m/s,the360msscenarioimplies0.126mtravelbeforedisplay,excludingbrakingorhumanresponse. Inference-onlyGPUbenchmarks cannotstandin forthispipeline.',['vision_latency_scenarios.csv'],['ENG_CAMERA','ENG_MJPEG','ENG_SCALED','ENG_ONNX'])
caption_text = json.loads((BASE/'engineering_caption_text.json').read_text(encoding='utf-8'))
for item in captions:
    item['caption'] = caption_text[item['id']].format(**CAP)
    if item['id']=='ENG_F02_solar':item['caption'] += ' The module power-temperature coefficient is −0.38% per kelvin.'
    if item['id']=='ENG_F07_tds':item['caption'] += ' The manufacturer full-scale limit is not a probabilistic standard uncertainty.'
    if item['id']=='ENG_F09_vision_latency':item['caption'] += ' Inference is assigned to a remote edge host; other pipeline time includes decoding, postprocessing and display.'
(OUT/'engineering_figure_captions.json').write_text(json.dumps(captions,indent=2),encoding='utf-8')
with (OUT/'engineering_figure_captions.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=['id','title','caption','evidence_status']);w.writeheader();w.writerows([{k:r[k] for k in w.fieldnames} for r in captions])
print('Created',len(captions),'compact figures, each SVG and 300 dpi PNG; analytical inputs unchanged')
