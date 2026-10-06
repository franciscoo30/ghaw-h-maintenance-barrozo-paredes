#!/usr/bin/env python3
"""Boxplots reproducibles de GHAW-H; PNG para insertar en Overleaf.

Cuartiles: pandas, interpolación lineal. Bigotes: Tukey (1.5 IQR).
El desplazamiento determinista de atípicos es perpendicular al eje de valores.
Ningún valor se modifica; el panel completo conserva todos los atípicos.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def stats(values, label):
    values = pd.Series(values).dropna().astype(float)
    q1, med, q3 = values.quantile([.25,.5,.75],interpolation='linear')
    iqr = q3-q1
    inside = values.between(q1-1.5*iqr,q3+1.5*iqr)
    return {'label':label,'n':int(len(values)), 'q1':float(q1),
            'med':float(med),'q3':float(q3),'whislo':float(values[inside].min()),
            'whishi':float(values[inside].max()),
            'fliers':sorted(values[~inside].tolist()),
            'minimum':float(values.min()),'maximum':float(values.max()),
            'iqr':float(iqr)}


def style_axis(ax):
    ax.set_axisbelow(True)
    ax.grid(axis='x',color='.88',linewidth=.45)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for spine in ['left','bottom']:
        ax.spines[spine].set_color('.35')
        ax.spines[spine].set_linewidth(.55)
    ax.tick_params(axis='both',length=2.5,width=.55,labelsize=7)
    ax.tick_params(axis='y',length=0,pad=5)


def boxes(ax,items,labels):
    positions=np.arange(len(items))
    ax.bxp(items,positions=positions,widths=.43,orientation='horizontal',
           showfliers=False,patch_artist=True,manage_ticks=False,
           boxprops={'edgecolor':'.12','facecolor':'.91','linewidth':.8},
           whiskerprops={'color':'.12','linewidth':.8},
           capprops={'color':'.12','linewidth':.8},
           medianprops={'color':'black','linewidth':1.3})
    for pos,item in zip(positions,items):
        vals=np.array(item['fliers'])
        # Orden fijo y dispersión determinista: conserva todas las repeticiones.
        jitter=np.random.default_rng(20261005+int(pos)).uniform(-.135,.135,len(vals))
        ax.scatter(vals,pos+jitter,s=7,facecolors='none',edgecolors='.45',
                   linewidths=.45,alpha=.8,zorder=2)
    ax.set_yticks(positions,labels=labels,fontsize=7)
    ax.set_ylim(len(items)-.55,-.55)
    style_axis(ax)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'paper/figuras')
    args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':7,
                         'axes.labelsize':7,'axes.titlesize':7.5,
                         'savefig.facecolor':'white'})
    tr=pd.read_csv(ROOT/'results/transitions.csv')
    active=tr.loc[tr.body_changed.astype(str).str.lower().eq('true')]
    assert len(active)==954
    metrics=[('body_added','Añadidas'),('body_deleted','Eliminadas'),('body_churn','Churn')]
    body=[stats(active[col],label) for col,label in metrics]
    labels=[x['label'] for x in body]
    fig,axes=plt.subplots(2,1,figsize=(3.6,2.65))
    fig.subplots_adjust(left=.23,right=.97,bottom=.19,top=.87,hspace=.62)
    fig.suptitle('Cambios del cuerpo: 954 transiciones',fontsize=8.3,y=.98)
    for ax in axes:boxes(ax,body,labels)
    axes[0].set_xlim(-2,80)
    axes[0].set_xticks([0,20,40,60,80])
    axes[0].set_title('(a) Detalle central: 0 a 80 líneas',loc='left',pad=3)
    axes[1].set_xlim(-12,650)
    axes[1].set_xticks([0,150,300,450,600])
    axes[1].set_title('(b) Rango completo',loc='left',pad=3)
    axes[1].set_xlabel('Líneas (escala lineal)',labelpad=2)
    fig.legend(handles=[Patch(facecolor='.91',edgecolor='.12',label='Caja: Q1-Q3'),
                        Line2D([0],[0],marker='o',color='none',markerfacecolor='none',
                               markeredgecolor='.45',markersize=3,label='Atípico')],
               loc='lower center',bbox_to_anchor=(.60,.005),ncol=2,frameon=False,
               fontsize=6.6,handlelength=1.2,columnspacing=1)
    fig.savefig(out/'boxplot_cambios.png',dpi=600)
    plt.close(fig)

    repo=pd.read_csv(ROOT/'results/repository_metrics.csv')
    groups=['TypeScript','Go','C#','Python','Makefile','F#']
    lang=[stats(repo.loc[repo.language.eq(g),'latest_body_loc_median'],g) for g in groups]
    assert [x['n'] for x in lang]==[52,41,32,29,21,18]
    fig,ax=plt.subplots(figsize=(3.6,2.45))
    fig.subplots_adjust(left=.32,right=.97,bottom=.18,top=.88)
    boxes(ax,lang,[f"{x['label']} (N={x['n']})" for x in lang])
    ax.set_xlim(-13,625)
    ax.set_xticks([0,100,200,300,400,500,600])
    ax.set_xlabel('Mediana de líneas del cuerpo por repositorio',labelpad=3)
    ax.set_title('Tamaño del cuerpo por contexto',fontsize=8.3,pad=9)
    for pos,item in enumerate(lang):
        if item['iqr']==0:
            ax.annotate('IQR = 0',xy=(item['med'],pos),
                        xytext=(item['med']+115,pos-.32),fontsize=6.4,
                        color='.35',ha='left',va='center',
                        arrowprops={'arrowstyle':'->','color':'.45','lw':.5})
    fig.savefig(out/'boxplot_lenguajes.png',dpi=600)
    plt.close(fig)
    report={'matplotlib':matplotlib.__version__,'pandas':pd.__version__,
            'quantiles':'linear','whiskers':'Tukey 1.5 IQR',
            'outlier_jitter':'deterministic, perpendicular only',
            'body_transitions':body,'repository_language_size':lang}
    (out/'boxplot_statistics.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('Imágenes verificadas contra 954 transiciones y los seis grupos de repositorios:',out)


if __name__=='__main__':main()
