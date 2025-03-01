import urllib

from backend.utils import Bunch
import pandas as pd
from pathlib import Path
import os
from enclave_wrangler.config import OUTDIR_DATASETS_TRANSFORMED, OUTDIR_OBJECTS
from functools import cache
from backend.utils import cnt, pdump
from enclave_wrangler.datasets import download_favorite_datasets as update_termhub_csets
from typing import Dict, List, Set

from enclave_wrangler.utils import make_objects_request

# from enclave_wrangler.dataset_upload import upload_new_container_with_concepts, upload_new_cset_version_with_concepts
# from enclave_wrangler.new_enclave_api import make_objects_request


DEBUG = True
PROJECT_DIR = Path(os.path.dirname(__file__)).parent
# TODO: Replace LFS implementation here with DB
# TODO: initialize if doesn't exist on start
# GLOBAL_DATASET_NAMES = list(FAVORITE_DATASETS.keys()) + ['concept_relationship_is_a']
GLOBAL_DATASET_NAMES = [
  'concept_set_members',
  'concept',
  'concept_relationship_subsumes_only',
  'concept_set_container',
  'code_sets',
  'concept_set_version_item',
  'deidentified_term_usage_by_domain_clamped',
  'concept_set_counts_clamped'
]
GLOBAL_OBJECT_DATASET_NAMES = [
  'researcher'
]


# Globals --------------------------------------------------------------------------------------------------------------


def load_dataset(ds_name, is_object=False) -> pd.DataFrame:
  """Load a local dataset CSV as a pandas DF"""
  csv_dir = OUTDIR_DATASETS_TRANSFORMED if not is_object else os.path.join(OUTDIR_OBJECTS, ds_name)
  path = os.path.join(csv_dir, ds_name + '.csv') if not is_object else os.path.join(csv_dir, 'latest.csv')
  print(f'loading: {path}')
  try:
    # tried just reading into pandas from sql tables --- incredibly slow!
    # ds = pd.read_sql_table(ds_name, CON, 'termhub_n3c')
    ds = pd.read_csv(path, keep_default_na=False)
  except Exception as err:
    print(f'failed loading {path}')
    raise err
  return ds


def filter(msg, ds, dfname, func, cols):
  df = ds.__dict__[dfname]
  before = { col: cnt(df[col]) for col in cols }

  ds.__dict__[dfname] = func(df)
  if ds.__dict__[dfname].equals(df):
    log_counts(f'{msg}. No change.', **before)
  else:
    log_counts(f'{msg}. Before', **before)
    after = { col: cnt(df[col]) for col in cols }
    log_counts(f'{msg}. After', **after)
    # change = { col: (after[col] - before[col]) / before[col] for col in cols }


def _log_counts():
  msgs = []
  def __log_counts(msg=None, concept_set_name=None, codeset_id=None, concept_id=None, print=False):
    if msg:
      msgs.append([msg, *[int(n) if n else None for n in [concept_set_name, codeset_id, concept_id]]])
    if (print):
      pdump(msgs)
    return msgs
  return __log_counts


log_counts = _log_counts()

DS = None  # Contains all the datasets as a dict
DS2 = None  # Contains all datasets, transformed datasets, and a few functions as a namespace

def load_globals():
  """
  expose tables and other stuff in namespace for convenient reference
      links                   # concept_relationship grouped by concept_id_1, subsumes only
      child_cids()            # function returning all the concept_ids that are
                              #   children (concept_id_1) of a concept_id
      connect_children()      # function returning concept hierarchy. see #139
                              #   (https://github.com/jhu-bids/TermHub/issues/139)
                              #   currently doing lists of tuples, will probably
                              #   switch to dict of dicts
  """
  ds = Bunch(DS)

  # TODO: try this later. will require filtering other stuff also? This will be useful for provenance
  # ds.data_messages = []
  other_msgs = []

  log_counts('concept_set_container', concept_set_name=cnt(ds.concept_set_container.concept_set_name))

  log_counts('code_sets',
             concept_set_name=cnt(ds.code_sets.concept_set_name),
             codeset_id=cnt(ds.code_sets.codeset_id))
  log_counts('concept_set_members',
             concept_set_name=cnt(ds.concept_set_members.concept_set_name),
             codeset_id=cnt(ds.concept_set_members.codeset_id),
             concept_id=cnt(ds.concept_set_members.concept_id))
  log_counts('concept_set_version_item',
             concept_set_name=cnt(ds.concept_set_members.concept_set_name),
             codeset_id=cnt(ds.concept_set_version_item.codeset_id),
             concept_id=cnt(ds.concept_set_version_item.concept_id))
  log_counts('intersection(containers, codesets)',
             concept_set_name=len(set.intersection(set(ds.concept_set_container.concept_set_name),
                                                   set(ds.code_sets.concept_set_name))))
  log_counts('intersection(codesets, members, version_items)',
             codeset_id=len(set.intersection(set(ds.code_sets.codeset_id),
                                             set(ds.concept_set_members.codeset_id),
                                             set(ds.concept_set_version_item.codeset_id))))
  log_counts('intersection(codesets, version_items)',
             codeset_id=len(set.intersection(set(ds.code_sets.codeset_id),
                                             set(ds.concept_set_version_item.codeset_id))))
  log_counts('intersection(members, version_items)',
             codeset_id=len(set.intersection(set(ds.concept_set_members.codeset_id),
                                             set(ds.concept_set_version_item.codeset_id))),
             concept_id=len(set.intersection(set(ds.concept_set_members.concept_id),
                                             set(ds.concept_set_version_item.concept_id))))

  codeset_ids = set(ds.concept_set_version_item.codeset_id)

  if len(set(ds.code_sets.codeset_id).difference(codeset_ids)):
    filter('weird that there would be versions (in code_sets and concept_set_members) '
           'that have nothing in concept_set_version_item...filtering those out',
           ds, 'code_sets', lambda df: df[df.codeset_id.isin(codeset_ids)], ['codeset_id'])

  if len(ds.concept_set_container) > cnt(ds.concept_set_container.concept_set_name):
    filter('concept_set_containers have duplicate items with different created_at and/or created_by. deleting all but most recent',
           ds, 'concept_set_container',
           lambda df: df.sort_values('created_at').groupby('concept_set_name').agg(lambda g: g.head(1)).reset_index(),
           ['concept_set_name'])


  # no change (2022-10-23):
  filter('concept_set_container filtered to exclude archived',
         ds, 'concept_set_container', lambda df: df[~ df.archived], ['concept_set_name'])

  #
  filter('concept_set_members filtered to exclude archived',
         ds, 'concept_set_members', lambda df: df[~ df.archived], ['codeset_id', 'concept_id'])

  concept_set_names = set.intersection(
    set(ds.concept_set_container.concept_set_name),
    set(ds.code_sets.concept_set_name))

  # csm_archived_names = set(DS['concept_set_members'][DS['concept_set_members'].archived].concept_set_name)
  # concept_set_names = concept_set_names.difference(csm_archived_names)

  # no change (2022-10-23):
  filter('concept_set_container filtered to have matching code_sets/versions',
         ds, 'concept_set_container', lambda df: df[df.concept_set_name.isin(concept_set_names)], ['concept_set_name'])

  filter('code_sets filtered to have matching concept_set_container',
         ds, 'code_sets', lambda df: df[df.concept_set_name.isin(concept_set_names)], ['concept_set_name'])

  codeset_ids = set.intersection(set(ds.code_sets.codeset_id),
                                 set(ds.concept_set_version_item.codeset_id))
  filter(
    'concept_set_members filtered to filtered code_sets', ds, 'concept_set_members',
    lambda df: df[df.codeset_id.isin(set(ds.code_sets.codeset_id))], ['codeset_id', 'concept_id'])

  # Filters out any concepts/concept sets w/ no name
  filter('concept_set_members filtered to exclude concept sets with empty names',
         ds, 'concept_set_members',
         lambda df: df[~df.archived],
         ['codeset_id', 'concept_id'])

  filter('concept_set_members filtered to exclude archived concept set.',
         ds, 'concept_set_members',
         lambda df: df[~df.archived],
         ['codeset_id', 'concept_id'])

  ds.concept_relationship = ds.concept_relationship_subsumes_only
  other_msgs.append('only using subsumes relationships in concept_relationship')

  # I don't know why, there's a bunch of codesets that have no concept_set_version_items:
  # >>> len(set(ds.concept_set_members.codeset_id))
  # 3733
  # >>> len(set(ds.concept_set_version_item.codeset_id))
  # 3021
  # >>> len(set(ds.concept_set_members.codeset_id).difference(set(ds.concept_set_version_item.codeset_id)))
  # 1926
  # should just toss them, right?

  # len(set(ds.concept_set_members.concept_id))             1,483,260
  # len(set(ds.concept_set_version_item.concept_id))          429,470
  # len(set(ds.concept_set_version_item.concept_id)
  #     .difference(set(ds.concept_set_members.concept_id)))   19,996
  #
  member_concepts = set(ds.concept_set_members.concept_id)
  #.difference(set(ds.concept_set_version_item))

  ds.concept_set_version_item = ds.concept_set_version_item[
    ds.concept_set_version_item.concept_id.isin(member_concepts)]

  # only need these two columns now:
  ds.concept_set_members = ds.concept_set_members[['codeset_id', 'concept_id']]

  ds.all_related_concepts = set(ds.concept_relationship.concept_id_1).union(
    set(ds.concept_relationship.concept_id_2))
  all_findable_concepts = member_concepts.union(ds.all_related_concepts)

  ds.concept.drop(['domain_id', 'vocabulary_id', 'concept_class_id', 'standard_concept', 'concept_code',
                   'invalid_reason', ], inplace=True, axis=1)

  ds.concept = ds.concept[ds.concept.concept_id.isin(all_findable_concepts)]

  ds.links = ds.concept_relationship.groupby('concept_id_1')
  # ds.all_concept_relationship_cids = set(ds.concept_relationship.concept_id_1).union(set(ds.concept_relationship.concept_id_2))

  @cache
  def get_container(concept_set_name):
    """This is for getting the RID of a dataset. This is available via the ontology API, not the dataset API.
    TODO: This needs caching, but the @cache decorator is not working."""
    return make_objects_request(f'objects/OMOPConceptSetContainer/{urllib.parse.quote(concept_set_name)}')

  @cache
  def child_cids(cid):
    """Return list of `concept_id_2` for each `concept_id_1` (aka all its children)"""
    if cid in ds.links.groups.keys():
      return [int(c) for c in ds.links.get_group(cid).concept_id_2.unique() if c != cid]
  ds.child_cids = child_cids

  # @cache
  def connect_children(pcid, cids):  # how to declare this should be tuple of int or None and list of ints
    if not cids:
      return None
    pcid in cids and cids.remove(pcid)
    pcid_kids = {int(cid): child_cids(cid) for cid in cids}
    # pdump({'kids': pcid_kids})
    return {cid: connect_children(cid, kids) for cid, kids in pcid_kids.items()}

  ds.connect_children = connect_children

  # Take codesets, and merge on container. Add to each version.
  # Some columns in codeset and container have the same name, so suffix is needed to distinguish them
  # ...The merge on `concept_set_members` is used for concept counts for each codeset version.
  #   Then adding cset usage counts
  all_csets = (
    ds
    .code_sets.merge(ds.concept_set_container, suffixes=['_version', '_container'],
                     on='concept_set_name')
    .merge(ds.concept_set_members
           .groupby('codeset_id')['concept_id']
           .nunique()
           .reset_index()
           .rename(columns={'concept_id': 'concepts'}), on='codeset_id')
    .merge(ds.concept_set_counts_clamped, on='codeset_id')
  )
  """
  all_csets columns:
  ['codeset_id', 'concept_set_version_title', 'project',
     'concept_set_name', 'source_application', 'source_application_version',
     'created_at_version', 'atlas_json', 'is_most_recent_version', 'version',
     'comments', 'intention_version', 'limitations', 'issues',
     'update_message', 'status_version', 'has_review', 'reviewed_by',
     'created_by_version', 'provenance', 'atlas_json_resource_url',
     'parent_version_id', 'authoritative_source', 'is_draft',
     'concept_set_id', 'project_id', 'assigned_informatician',
     'assigned_sme', 'status_container', 'stage', 'intention_container',
     'n3c_reviewer', 'alias', 'archived', 'created_by_container',
     'created_at_container', 'concepts', 'approx_distinct_person_count',
     'approx_total_record_count'],
  had been dropping all these and all the research UIDs... should
    start doing stuff with that info.... had just been looking for ways 
    to make data smaller.... 
  
  all_csets = all_csets.drop([
    'parent_version_id', 'concept_set_name', 'source_application', 
    'is_draft', 'project', 'atlas_json', 'created_at_container', 
    'source_application_version', 'version', 'comments', 'alias', 
    'concept_set_id', 'created_at_version', 'atlas_json_resource_url'])
  """

  all_csets = all_csets.drop_duplicates()
  ds.all_csets = all_csets

  print('added usage counts to code_sets')

  """
      Term usage is broken down by domain and some concepts appear in multiple domains.
      (each concept has only one domain_id in the concept table, but the same concept might
      appear in condition_occurrence and visit and procedure, so it would have usage counts
      in multiple domains.) We can sum total_counts across domain, but not distinct_person_counts
      (possible double counting). So, for now at least, distinct_person_count will appear as a 
      comma-delimited list of counts -- which, of course, makes it hard to use in visualization.
      Maybe we should just use the domain with the highest distinct person count? Not sure.
  """
  # df = df[df.concept_id.isin([9202, 9201])]
  domains = {
    'drug_exposure': 'd',
    'visit_occurrence': 'v',
    'observation': 'o',
    'condition_occurrence': 'c',
    'procedure_occurrence': 'p',
    'measurement': 'm'
  }
  # ds.deidentified_term_usage_by_domain_clamped['domain'] = \
  #     [domains[d] for d in ds.deidentified_term_usage_by_domain_clamped.domain]

  g = ds.deidentified_term_usage_by_domain_clamped.groupby(['concept_id'])
  concept_usage_counts = (
    g.size().to_frame(name='domain_cnt')
    .join(g.agg(
      total_count=('total_count', sum),
      domain=('domain', ','.join),
      distinct_person_count=('distinct_person_count', lambda x: ','.join([str(c) for c in x]))
    ))
    .reset_index())
  print('combined usage counts across domains')

  # c = ds.concept.reset_index()
  # cs = c[c.concept_id.isin([9202, 9201, 4])]

  # h = [r[1] for r in ds.deidentified_term_usage_by_domain_clamped.head(3).iterrows()]
  # [{r.domain: {'records': r.total_count, 'patients': r.distinct_person_count}} for r in h]
  ds.concept = (
    ds.concept.drop(['valid_start_date','valid_end_date'], axis=1)
    .merge(concept_usage_counts, on='concept_id', how='left')
    .fillna({'domain_cnt': 0, 'domain': '', 'total_count': 0, 'distinct_person_count': 0})
    .astype({'domain_cnt': int, 'total_count': int})
    # .set_index('concept_id')
  )
  print('Done building global ds objects')

  return ds


def disabling_globals():
  # todo: consider: run 2 backend servers, 1 to hold the data and 1 to service requests / logic? probably.
  # TODO: #2: remove try/except when git lfs fully set up
  # todo: temp until we decide if this is the correct way
  try:
    DS = {
      **{name: load_dataset(name) for name in GLOBAL_DATASET_NAMES},
      **{name: load_dataset(name, is_object=True) for name in GLOBAL_OBJECT_DATASET_NAMES},
    }
    DS2 = load_globals()
    #  TODO: Fix this warning? (Joe: doing so will help load faster, actually)
    #   DtypeWarning: Columns (4) have mixed types. Specify dtype option on import or set low_memory=False.
    #   keep_default_na fixes some or all the warnings, but doesn't manage dtypes well.
    #   did this in termhub-csets/datasets/fixing-and-paring-down-csv-files.ipynb:
    #   csm = pd.read_csv('./concept_set_members.csv',
    #                    # dtype={'archived': bool},    # doesn't work because of missing values
    #                   converters={'archived': lambda x: x and True or False}, # this makes it a bool field
    #                   keep_default_na=False)
  except FileNotFoundError:
    # todo: what if they haven't downloaded? maybe need to ls files and see if anything needs to be downloaded first
    # TODO: objects should be updated too
    update_termhub_csets(transforms_only=True)
    DS = {
      **{name: load_dataset(name) for name in GLOBAL_DATASET_NAMES},
      **{name: load_dataset(name, is_object=True) for name in GLOBAL_OBJECT_DATASET_NAMES},
    }
    DS2 = load_globals()
  print(f'Favorite datasets loaded: {list(DS.keys())}')


# Utility functions ----------------------------------------------------------------------------------------------------
# @cache
def data_stuff_for_codeset_ids(codeset_ids):
  """
  for specific codeset_ids:
      subsets of tables:
          df_code_set_i
          df_concept_set_members_i
          df_concept_relationship_i
      and other stuff:
          concept_ids             # union of all the concept_ids across the requested codesets
          related                 # sorted list of related concept sets
          codesets_by_concept_id  # lookup codeset_ids a concept_id belongs to (in dsi instead of ds because of possible performance impacts)
          top_level_cids          # concepts in selected codesets that have no parent concepts in this group
          cset_name_columns       #

  """
  dsi = Bunch({})

  print(f'data_stuff_for_codeset_ids({codeset_ids})')

  # Vocab table data
  dsi.code_sets_i = DS2.code_sets[DS2.code_sets['codeset_id'].isin(codeset_ids)]
  dsi.concept_set_members_i = DS2.concept_set_members[DS2.concept_set_members['codeset_id'].isin(codeset_ids)]
  # - version items
  dsi.concept_set_version_item_i = DS2.concept_set_version_item[DS2.concept_set_version_item['codeset_id'].isin(codeset_ids)]
  flags = ['includeDescendants', 'includeMapped', 'isExcluded']
  dsi.concept_set_version_item_i = dsi.concept_set_version_item_i[['codeset_id', 'concept_id', *flags]]
  # doesn't work if df is empty
  if len(dsi.concept_set_version_item_i):
    dsi.concept_set_version_item_i['item_flags'] = dsi.concept_set_version_item_i.apply(
      lambda row: (', '.join([f for f in flags if row[f]])), axis=1)
  else:
    dsi.concept_set_version_item_i = dsi.concept_set_version_item_i.assign(item_flags='')
  dsi.concept_set_version_item_i = dsi.concept_set_version_item_i[['codeset_id', 'concept_id', 'item_flags']]
  # - cset member items
  dsi.cset_members_items = \
    dsi.concept_set_members_i.assign(csm=True).merge(
      dsi.concept_set_version_item_i.assign(item=True),
      on=['codeset_id', 'concept_id'], how='outer', suffixes=['_l','_r']
    ).fillna({'item_flags': '', 'csm': False, 'item': False})

  # - selected csets and relationships
  selected_concept_ids: Set[int] = set.union(set(dsi.cset_members_items.concept_id))
  dsi.concept_relationship_i = DS2.concept_relationship[
    (DS2.concept_relationship.concept_id_1.isin(selected_concept_ids)) &
    (DS2.concept_relationship.concept_id_2.isin(selected_concept_ids)) &
    (DS2.concept_relationship.concept_id_1 != DS2.concept_relationship.concept_id_2)
    # & (ds.concept_relationship.relationship_id == 'Subsumes')
    ]

  # Get related codeset IDs
  related_codeset_ids: Set[int] = set(DS2.concept_set_members[
                                        DS2.concept_set_members.concept_id.isin(selected_concept_ids)].codeset_id)
  dsi.related_csets = (
    DS2.all_csets[DS2.all_csets['codeset_id'].isin(related_codeset_ids)]
    .merge(DS2.concept_set_members, on='codeset_id')
    .groupby(list(DS2.all_csets.columns))['concept_id']
    .agg(intersecting_concepts=lambda x: len(set(x).intersection(selected_concept_ids)))
    .reset_index()
    .convert_dtypes({'intersecting_concept_ids': 'int'})
    .assign(recall=lambda row: row.intersecting_concepts / len(selected_concept_ids),
            precision=lambda row: row.intersecting_concepts / row.concepts,
            selected= lambda row: row.codeset_id.isin(codeset_ids))
    .sort_values(by=['selected', 'concepts'], ascending=False)
  )
  dsi.selected_csets = dsi.related_csets[dsi.related_csets['codeset_id'].isin(codeset_ids)]

  # Researchers
  researcher_cols = ['created_by_container', 'created_by_version', 'assigned_sme', 'reviewed_by', 'n3c_reviewer',
                     'assigned_informatician']
  researcher_ids = set()
  for i, row in dsi.selected_csets.iterrows():
    for _id in [row[col] for col in researcher_cols if hasattr(row, col) and row[col]]:
      researcher_ids.add(_id)
  researchers: List[Dict] = DS2.researcher[DS2.researcher['multipassId'].isin(researcher_ids)].to_dict(orient='records')
  dsi.selected_csets['researchers'] = researchers

  # Selected cset RIDs
  dsi.selected_csets['rid'] = [get_container(name)['rid'] for name in dsi.selected_csets.concept_set_name]

  # Get relationships for selected code sets
  dsi.links = dsi.concept_relationship_i.groupby('concept_id_1')

  # Get child `concept_id`s
  @cache
  def child_cids(cid):
    """Closure for geting child concept IDs"""
    if cid in dsi.links.groups.keys():
      return [int(c) for c in dsi.links.get_group(cid).concept_id_2.unique() if c != cid]
  dsi.child_cids = child_cids

  # @cache
  def connect_children(pcid, cids):  # how to declare this should be tuple of int or None and list of ints
    if not cids:
      return None
    pcid in cids and cids.remove(pcid)
    pcid_kids = {int(cid): child_cids(cid) for cid in cids}
    # pdump({'kids': pcid_kids})
    return {cid: connect_children(cid, kids) for cid, kids in pcid_kids.items()}
  dsi.connect_children = connect_children

  # Top level concept IDs for the root of our flattened hierarchy
  dsi.top_level_cids = (set(selected_concept_ids).difference(set(dsi.concept_relationship_i.concept_id_2)))

  dsi.hierarchy = h = dsi.connect_children(-1, dsi.top_level_cids)

  leaf_cids = set([])
  if h:
    leaf_cids = set([int(str(k).split('.')[-1]) for k in pd.json_normalize(h).to_dict(orient='records')[0].keys()])
  dsi.concepts = DS2.concept[DS2.concept.concept_id.isin(leaf_cids.union(set(dsi.cset_members_items.concept_id)))]

  return dsi
