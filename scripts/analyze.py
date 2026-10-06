#!/usr/bin/env python3
"""Reproduce the preliminary descriptive analysis of GHAW-H.

Units: observed history, version, linked consecutive transition, repository.
Lines are physical text lines (including empty lines), using str.splitlines().
Consecutive transitions follow predecessor links and are audited against rank;
timestamps are NOT used to reorder histories. Diffs use SequenceMatcher with
autojunk=False, counting a replacement as both added and deleted lines.
"""
import hashlib
import json
import platform
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
TABLES = ["lock_file_snapshot", "repository", "source_markdown_file_history",
          "source_markdown_file_snapshot", "source_markdown_file_version"]
PKS = {t: f"{t}_id" for t in TABLES}


def lines(text):
    assert isinstance(text, str), "Missing/nonstring text needs an explicit missingness rule"
    return text.splitlines()


def diff_metrics(old, new):
    a, b = lines(old), lines(new)
    added = deleted = 0
    for tag, i, j, k, l in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            deleted += j - i
        if tag in ("replace", "insert"):
            added += l - k
    return added, deleted


def describe(series):
    s = pd.Series(series).dropna()
    if s.empty:
        return {"n": 0}
    return {"n": int(len(s)), "min": float(s.min()), "q1": float(s.quantile(.25)),
            "median": float(s.median()), "q3": float(s.quantile(.75)),
            "max": float(s.max()), "mean": float(s.mean())}


def median(series):
    return float(series.median()) if series.notna().any() else np.nan


def main():
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text())
    df = {}
    for table in TABLES:
        p = ROOT / "data" / "raw" / f"{table}.parquet"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == manifest["files"][table]["sha256"]
        df[table] = pd.read_parquet(p)
        assert df[table][PKS[table]].notna().all()
        assert df[table][PKS[table]].is_unique
    # Preserve original Parquet dtypes before nullable-link or timestamp conversions.
    dtypes = {t:{c:str(v) for c,v in frame.dtypes.items()} for t,frame in df.items()}
    repo, histories, snap, versions, locks = (df[t] for t in ["repository", "source_markdown_file_history",
                                                           "source_markdown_file_snapshot", "source_markdown_file_version",
                                                           "lock_file_snapshot"])
    vid = "source_markdown_file_version_id"
    hid = "source_markdown_file_history_id"
    sid = "source_markdown_file_snapshot_id"
    pred = "predecessor_source_markdown_file_version_id"
    succ = "successor_source_markdown_file_version_id"
    assert versions[hid].isin(histories[hid]).all()
    assert versions[sid].isin(snap[sid]).all()
    assert snap.repository_id.isin(repo.repository_id).all()
    assert locks[vid].isin(versions[vid]).all()
    assert versions[sid].is_unique and locks[vid].is_unique
    assert len(locks) == len(versions) == len(snap)
    assert versions.groupby(hid).size().sort_index().equals(histories.set_index(hid).version_count.sort_index())
    assert versions.groupby(hid)["rank"].apply(lambda x: sorted(x) == list(range(1, len(x)+1))).all()
    for col in [pred, succ]:
        versions[col] = versions[col].astype("Int64")
        assert versions[col].dropna().isin(versions[vid]).all()
    versions["timestamp"] = pd.to_datetime(versions.committed_at, utc=True, errors="raise")
    assert versions["timestamp"].notna().all(), "Every observed version needs a valid timestamp"
    obs = versions.merge(snap, on=sid, validate="one_to_one").merge(repo, on="repository_id", validate="many_to_one")
    obs["language"] = obs.main_language.fillna("Unknown").replace("", "Unknown")
    by_version = obs.set_index(vid)
    assert obs.groupby(hid).repository_id.nunique().eq(1).all()
    assert obs.groupby(hid).path.nunique().eq(1).all()
    assert obs.loc[obs["rank"].eq(1), pred].isna().all()
    assert obs.loc[obs["rank"].gt(1), pred].notna().all()
    ordered = obs.sort_values([hid, "rank"])
    assert ordered.groupby(hid).tail(1)[succ].isna().all()
    assert ordered.groupby(hid).head(-1)[succ].notna().all()
    for textcol in ["content", "body", "frontmatter"]:
        assert obs[textcol].notna().all()
        obs[f"{textcol}_loc"] = obs[textcol].map(lambda x:len(lines(x)))
        obs[f"{textcol}_nonblank_loc"] = obs[textcol].map(lambda x:sum(bool(l.strip()) for l in lines(x)))
    transitions = []
    for row in obs.loc[obs[pred].notna()].itertuples(index=False):
        new = row._asdict()
        old = by_version.loc[int(new[pred])]
        assert old[hid] == new[hid] and old["rank"] + 1 == new["rank"]
        assert int(old[succ]) == new[vid]
        t = {"old_version_id": int(new[pred]), "new_version_id": int(new[vid]),
             hid: int(new[hid]), "repository_id": int(new["repository_id"]),
             "repo_full_name": new["repo_full_name"], "path": new["path"],
             "language": new["language"], "old_committed_at": old.committed_at,
             "new_committed_at": new["committed_at"],
             "elapsed_days": (new["timestamp"] - old.timestamp).total_seconds()/86400}
        for textcol in ["content", "body", "frontmatter"]:
            added, deleted = diff_metrics(old[textcol], new[textcol])
            nold, nnew = len(lines(old[textcol])), len(lines(new[textcol]))
            t.update({f"{textcol}_old_loc":nold, f"{textcol}_new_loc":nnew,
                      f"{textcol}_added":added, f"{textcol}_deleted":deleted,
                      f"{textcol}_churn":added+deleted, f"{textcol}_net":nnew-nold,
                      f"{textcol}_relative_churn":(added+deleted)/max(1,nold),
                      f"{textcol}_changed":added+deleted>0,
                      f"{textcol}_text_changed":old[textcol] != new[textcol]})
            assert nnew - nold == added - deleted
        transitions.append(t)
    tr = pd.DataFrame(transitions)
    assert len(tr) == len(versions)-len(histories)
    obs.drop(columns=["content", "body", "frontmatter", "timestamp"]).to_csv(OUT / "version_features.csv", index=False)
    tr.to_csv(OUT / "transitions.csv", index=False)
    # An effective body change may follow several configuration-only versions.
    # Measure from rank 1 to the first body change and between later body changes,
    # NOT simply between the immediately adjacent source-version timestamps.
    body_events = []
    body_changed_ids = set(tr.loc[tr.body_changed, "new_version_id"])
    for history_id, g in ordered.groupby(hid):
        origin = g.iloc[0]
        for _, new in g.iloc[1:].iterrows():
            if new[vid] in body_changed_ids:
                body_events.append({hid:int(history_id), "repository_id":int(new.repository_id),
                    "language":new.language, "origin_version_id":int(origin[vid]),
                    "new_version_id":int(new[vid]), "origin_rank":int(origin["rank"]),
                    "new_rank":int(new["rank"]), "origin_committed_at":origin.committed_at,
                    "new_committed_at":new.committed_at,
                    "elapsed_days":(new.timestamp-origin.timestamp).total_seconds()/86400,
                    "skipped_versions":int(new["rank"]-origin["rank"]-1),
                    "first_event_in_history":bool(origin["rank"]==1)})
                origin = new
    be = pd.DataFrame(body_events)
    assert len(be) == int(tr.body_changed.sum())
    assert be.elapsed_days.ge(0).all()
    be.to_csv(OUT / "body_change_events.csv",index=False)
    hs = ordered.groupby(hid).agg(repository_id=("repository_id", "first"),
          repo_full_name=("repo_full_name", "first"), language=("language", "first"),
          path=("path", "first"), versions=(vid, "size"),
          first_committed_at=("committed_at", "first"), last_committed_at=("committed_at", "last"),
          first_timestamp=("timestamp", "first"), last_timestamp=("timestamp", "last"))
    hs["span_days"] = (hs.last_timestamp-hs.first_timestamp).dt.total_seconds()/86400
    tc = tr.groupby(hid).agg(transitions=("new_version_id", "size"),
         changed_transitions=("content_changed", "sum"), body_changed_transitions=("body_changed", "sum"),
         frontmatter_changed_transitions=("frontmatter_changed", "sum"))
    hs = hs.join(tc).fillna({"transitions":0, "changed_transitions":0,
                            "body_changed_transitions":0, "frontmatter_changed_transitions":0})
    hs["has_effective_change"] = hs.changed_transitions.gt(0)
    hs["has_body_effective_change"] = hs.body_changed_transitions.gt(0)
    hs.drop(columns=["first_timestamp", "last_timestamp"]).to_csv(OUT / "history_metrics.csv")
    latest = obs.sort_values([hid, "rank"]).groupby(hid).tail(1)
    rm = repo.copy().set_index("repository_id")
    rm["language"] = rm.main_language.fillna("Unknown").replace("", "Unknown")
    rm = rm.join(hs.groupby("repository_id").agg(histories=("versions", "size"),
          versions=("versions", "sum"), multiversion_histories=("versions", lambda x:int((x>1).sum())),
          changed_histories=("has_effective_change", "sum"),
          body_changed_histories=("body_changed_transitions",lambda x:int(x.gt(0).sum())),
          frontmatter_changed_histories=("frontmatter_changed_transitions",lambda x:int(x.gt(0).sum()))))
    rm["changed_history_share"] = rm.changed_histories/rm.histories
    rm["body_changed_history_share"] = rm.body_changed_histories/rm.histories
    rm = rm.join(latest.groupby("repository_id").agg(latest_content_loc_median=("content_loc", "median"),
             latest_body_loc_median=("body_loc", "median"), latest_frontmatter_loc_median=("frontmatter_loc", "median")))
    for textcol in ["content", "body", "frontmatter"]:
        active = tr.loc[tr[f"{textcol}_changed"]]
        metrics = active.groupby("repository_id").agg(**{
            f"{textcol}_changed_transitions":("new_version_id", "size"),
            f"{textcol}_churn_median":(f"{textcol}_churn", "median"),
            f"{textcol}_relative_churn_median":(f"{textcol}_relative_churn", "median"),
            f"{textcol}_net_median":(f"{textcol}_net", "median")})
        rm = rm.join(metrics)
        rm[f"{textcol}_changed_transitions"] = rm[f"{textcol}_changed_transitions"].fillna(0).astype(int)
    valid_interval = tr.loc[tr.elapsed_days.ge(0)]
    rm = rm.join(tr.groupby("repository_id").size().rename("transitions"))
    rm["transitions"] = rm.transitions.fillna(0).astype(int)
    rm = rm.join(valid_interval.groupby("repository_id").elapsed_days.median().rename("interval_days_median"))
    rm = rm.join(be.groupby("repository_id").elapsed_days.median().rename("body_event_interval_days_median"))
    rm["changed_transition_share"] = rm.content_changed_transitions/rm.transitions.replace(0,np.nan)
    rm.to_csv(OUT / "repository_metrics.csv")
    ls = []
    for language, g in rm.groupby("language"):
        rg = tr.loc[tr.repository_id.isin(g.index)]
        lg = latest.loc[latest.repository_id.isin(g.index)]
        d = {"language":language, "repositories":len(g), "histories":int(g.histories.sum()),
             "versions":int(g.versions.sum()), "transitions":int(g.transitions.sum()),
             "repositories_with_transition":int(g.transitions.gt(0).sum()),
             "repositories_with_effective_change":int(g.content_changed_transitions.gt(0).sum()),
             "repositories_with_body_change":int(g.body_changed_transitions.gt(0).sum()),
             "histories_with_body_change":int(g.body_changed_histories.sum()),
             "body_changed_transitions":int(rg.body_changed.sum()),
             "changed_transitions":int(rg.content_changed.sum()),
             "median_repo_changed_history_share":float(g.changed_history_share.median()),
             "median_repo_body_changed_history_share":median(g.body_changed_history_share),
             "median_repo_changed_transition_share":median(g.changed_transition_share),
             "median_repo_latest_content_loc":float(g.latest_content_loc_median.median()),
             "median_repo_latest_body_loc":float(g.latest_body_loc_median.median()),
             "median_repo_effective_content_churn":median(g.content_churn_median),
             "median_repo_effective_body_churn":median(g.body_churn_median),
             "median_repo_effective_relative_churn":median(g.content_relative_churn_median),
             "median_repo_interval_days":median(g.interval_days_median),
             "median_repo_body_event_interval_days":median(g.body_event_interval_days_median),
             "pooled_latest_content_loc_median":float(lg.content_loc.median()),
             "pooled_effective_churn_median":median(rg.loc[rg.content_changed,"content_churn"]),
             "pooled_nonnegative_interval_median":median(rg.loc[rg.elapsed_days.ge(0),"elapsed_days"])}
        ls.append(d)
    language_summary = pd.DataFrame(ls).sort_values("repositories",ascending=False)
    language_summary.to_csv(OUT / "language_summary.csv",index=False)
    no_pulumi = rm.loc[rm.repo_owner.ne("pulumi")]
    no_pulumi.groupby("language").agg(repositories=("repo_full_name","size"),
        repositories_with_body_change=("body_changed_transitions",lambda x:int(x.gt(0).sum())),
        median_repo_latest_body_loc=("latest_body_loc_median","median"),
        median_repo_latest_content_loc=("latest_content_loc_median","median"),
        median_repo_effective_body_churn=("body_churn_median","median"),
        median_repo_effective_content_churn=("content_churn_median","median")).to_csv(OUT / "language_sensitivity_without_pulumi.csv")
    latest = latest.copy()
    latest["has_imports_field"] = latest.frontmatter.str.contains(r"(?m)^imports\s*:",regex=True)
    latest["one_line_body"] = latest.body_loc.le(1)
    latest.drop(columns=["content", "frontmatter", "body", "timestamp"]).to_csv(OUT / "latest_version_features.csv",index=False)
    latest.groupby("language").agg(histories=(hid,"size"),
        imports_field_histories=("has_imports_field","sum"),one_line_body_histories=("one_line_body","sum")).to_csv(OUT / "language_imports_audit.csv")
    obs.loc[obs.repo_full_name.eq("apache/cloudstack"),[vid,hid,sid,"rank","committed_at",pred,succ,"repo_full_name","main_language","path","content_loc","body_loc","frontmatter_loc"]].to_csv(OUT / "dataset_evidence_example.csv",index=False)
    known_languages = repo.main_language.dropna().replace("",np.nan).dropna()
    effective = tr.loc[tr.content_changed]
    summary = {"dataset":manifest["dataset"], "revision":manifest["revision"],
        "environment":{"python":platform.python_version(),"pandas":pd.__version__,"numpy":np.__version__,"pyarrow":pyarrow.__version__},
        "table_rows":{t:len(f) for t,f in df.items()},"schema":dtypes,
        "versions_start_utc":str(obs.timestamp.min()),"versions_end_utc":str(obs.timestamp.max()),
        "repositories":len(repo),"histories":len(histories),"versions":len(versions),"transitions":len(tr),
        "repository_path_pairs":int(snap[["repository_id","path"]].drop_duplicates().shape[0]),
        "multiversion_histories":int((histories.version_count>1).sum()),
        "histories_with_effective_change":int(hs.has_effective_change.sum()),
        "histories_with_body_change":int(hs.body_changed_transitions.gt(0).sum()),
        "histories_with_frontmatter_change":int(hs.frontmatter_changed_transitions.gt(0).sum()),
        "repositories_with_transition":int(rm.transitions.gt(0).sum()),
        "repositories_with_effective_change":int(rm.content_changed_transitions.gt(0).sum()),
        "repositories_with_body_change":int(rm.body_changed_transitions.gt(0).sum()),
        "repositories_with_frontmatter_change":int(rm.frontmatter_changed_transitions.gt(0).sum()),
        "histories_version_count":describe(histories.version_count),
        "history_span_days":describe(hs.span_days),
        "history_span_days_multiversion":describe(hs.loc[hs.versions.gt(1),"span_days"]),
        "language_known_repositories":len(known_languages),"language_unknown_repositories":len(repo)-len(known_languages),
        "language_count_known":int(known_languages.nunique()),
        "effective_transitions":len(effective),"zero_line_churn_transitions":int((~tr.content_changed).sum()),
        "raw_text_changed_line_unchanged_transitions":int((tr.content_text_changed & ~tr.content_changed).sum()),
        "raw_text_changed_line_unchanged_by_component":{
            textcol:int((tr[f"{textcol}_text_changed"]&~tr[f"{textcol}_changed"]).sum())
            for textcol in ["content","body","frontmatter"]},
        "effective_transition_share":float(tr.content_changed.mean()),
        "negative_time_intervals":int(tr.elapsed_days.lt(0).sum()),"zero_time_intervals":int(tr.elapsed_days.eq(0).sum()),
        "nonnegative_interval_days":describe(valid_interval.elapsed_days),
        "effective_nonnegative_interval_days":describe(tr.loc[tr.elapsed_days.ge(0)&tr.content_changed,"elapsed_days"]),
        "body_change_event_intervals_days":describe(be.elapsed_days),
        "body_change_event_intervals_between_changes_days":describe(be.loc[~be.first_event_in_history,"elapsed_days"]),
        "body_change_event_intervals_first_change_days":describe(be.loc[be.first_event_in_history,"elapsed_days"]),
        "body_change_events_skipping_yaml_only_versions":int(be.skipped_versions.gt(0).sum()),
        "effective_growth_transitions":int(effective.content_net.gt(0).sum()),
        "effective_shrink_transitions":int(effective.content_net.lt(0).sum()),
        "effective_equal_size_transitions":int(effective.content_net.eq(0).sum()),
        "body_effective_growth_transitions":int((tr.body_changed&tr.body_net.gt(0)).sum()),
        "body_effective_shrink_transitions":int((tr.body_changed&tr.body_net.lt(0)).sum()),
        "body_effective_equal_size_transitions":int((tr.body_changed&tr.body_net.eq(0)).sum()),
        "body_only_line_changes":int((tr.body_changed & ~tr.frontmatter_changed).sum()),
        "frontmatter_only_line_changes":int((~tr.body_changed & tr.frontmatter_changed).sum()),
        "both_body_frontmatter_line_changes":int((tr.body_changed & tr.frontmatter_changed).sum()),
        "content_changed_neither_component_changed":int((tr.content_changed & ~tr.body_changed & ~tr.frontmatter_changed).sum()),
        "latest_versions_with_imports_field":int(latest.has_imports_field.sum()),
        "latest_versions_with_one_line_body":int(latest.one_line_body.sum()),
        "latest_versions_with_one_line_body_and_imports":int((latest.one_line_body&latest.has_imports_field).sum()),
        "latest_distinct_content_strings":int(latest.content.nunique()),
        "repositories_by_owner":repo.repo_owner.value_counts().to_dict(),
        "integrity_checks_passed":["unique primary keys","complete foreign keys","1:1 snapshot-version-lock",
            "history version_count equals observed count","contiguous ranks","complete reciprocal links",
            "one repository and path per history","diff net equals LOC delta"],
        "sha256_files":{t:manifest["files"][t]["sha256"] for t in TABLES},
        "metrics":{}}
    for textcol in ["content", "body", "frontmatter"]:
        act = tr.loc[tr[f"{textcol}_changed"]]
        summary["metrics"][textcol] = {"all_version_loc":describe(obs[f"{textcol}_loc"]),
            "raw_text_changed_line_unchanged_transitions":int((tr[f"{textcol}_text_changed"]&~tr[f"{textcol}_changed"]).sum()),
            "latest_history_loc":describe(latest[f"{textcol}_loc"]),
            "latest_repo_loc_median":describe(rm[f"latest_{textcol}_loc_median"]),
            "changed_transitions":len(act), "all_transition_churn":describe(tr[f"{textcol}_churn"]),
            "effective_churn":describe(act[f"{textcol}_churn"]),
            "effective_added":describe(act[f"{textcol}_added"]),
            "effective_deleted":describe(act[f"{textcol}_deleted"]),
            "effective_net":describe(act[f"{textcol}_net"]),
            "effective_relative_churn":describe(act[f"{textcol}_relative_churn"]),
            "sum_added":int(tr[f"{textcol}_added"].sum()),"sum_deleted":int(tr[f"{textcol}_deleted"].sum())}
    (OUT / "summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:summary[k] for k in ["revision","repositories","histories","versions","transitions",
        "histories_with_body_change","repositories_with_body_change","body_only_line_changes",
        "frontmatter_only_line_changes","both_body_frontmatter_line_changes"]},indent=2))
    print(language_summary[["language","repositories","repositories_with_body_change",
        "median_repo_latest_body_loc","median_repo_effective_body_churn"]].head(10).to_string(index=False))
    print("All audit checks passed; outputs:",OUT)


if __name__ == "__main__":
    main()
