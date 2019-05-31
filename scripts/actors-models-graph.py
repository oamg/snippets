#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import sys

from collections import namedtuple
from leapp.repository.scan import find_and_scan_repositories

def serializable_tags():
    '''Check if Tag has serializable class method and if not monkeypatch it.'''
    from leapp.tags import Tag
    try:
        Tag.serializable()
    except AttributeError:
        print('Patching leapp Tags', file=sys.stderr)

        def serialize(cls):
            return {'name': cls.__name__}
        Tag.serialize = classmethod(serialize)
        print('Done', file=sys.stderr)


def basic_graph(actors, model_consumers, missing_producer_actors, missing_consumer_actors, file_handle):
    """
    Create basic directed graph with actors as nodes and models as edges.

    If there are some models that are not produced/consumed by any actor, dummy
    actor is created its color is set to red.
    """
    for actor in actors:
        for model in actor.produces:
            for consumer in model_consumers[model]:
                line = '\t{producer} -> {consumer} [xlabel={model}];\n'.format(producer=actor.name,
                                                                              consumer=consumer,
                                                                              model=model)
                file_handle.write(line)

    # colorize missing actors that produce certain models
    file_handle.write('\n\t// colorize missing actors that produce certain models\n')
    for actor in missing_producer_actors:
        file_handle.write('\t{actor} [color=red, fontcolor=red]\n'.format(actor=actor.name))

    # colorize missing actors that consume certain models
    file_handle.write('\n\t// colorize missing actors that consume certain models\n')
    for actor in missing_consumer_actors:
        file_handle.write('\t{actor} [color=red, fontcolor=red]\n'.format(actor=actor.name))

def node_distance(file_handle):
    """Add parameters setting bigger distance between nodes."""
    file_handle.write('\n')
    file_handle.write('\tranksep = "2";\n')
    file_handle.write('\tnodesep="2";\n')

def same_rank(actors, file_handle):
    """Set same rank (all nodes in one row/column) for all actors."""
    file_handle.write('\n\t\t{\n')
    file_handle.write('\t\t\trank=same;\n')
    file_handle.write('\t\t\t' + ',\n\t\t\t'.join(actors))
    file_handle.write('\n\t\t}\n')

def clusters(tags, file_handle):
    """
    Create clusters from actors sharing the same tag.

    The cluster's border and header color is set to blue.
    Edges presentation is set to 'ortho' to avoid problems with overlapping.
    """
    file_handle.write('\n')
    file_handle.write('\tsplines="ortho";\n')
    for tag in tags:
        file_handle.write('\tsubgraph cluster_{tag} {{\n'.format(tag=tag))
        for actor in tags[tag]:
            file_handle.write('\t\t{actor};\n'.format(actor=actor))
        file_handle.write('\n\t\tlabel={tag};\n'.format(tag=tag))

        same_rank(tags[tag], file_handle)

        file_handle.write('\n\t\tcolor=blue;\n')
        file_handle.write('\t\tfontcolor=blue;\n')

        file_handle.write('\t}\n')

if __name__ == '__main__':
    description = 'Generate a dot file describing dependencies between actors and models.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-r', '--repo', required=True, help='path to repository with actors')
    parser.add_argument('-d', '--dot', default='graph.dot', help='path to a dot file that should be generated')
    tag_help = 'cluster actors by tags\nWARNING: the edges are too close to each other, so it is usually hard to say which label belongs to which edge'
    parser.add_argument('-t', '--tags', default=False, action='store_true', help=tag_help)
    args = parser.parse_args()

    if os.path.exists(args.dot):
        print('Already exists: {path}'.format(path=args.dot), file=sys.stderr)
        sys.exit(1)

    #repository = find_and_scan_repositories('leapp-repository/repos/system_upgrade/el7toel8/', include_locals=True)
    repository = find_and_scan_repositories(args.repo, include_locals=True)
    if not repository:
        print('Could not find repository in specified path: {path}'.format(path=args.repo), file=sys.stderr)
        sys.exit(1)
    try:
        repository.load()
    except Exception as e:
        print('Could not load repository:\n{message}'.format(message=e.message), file=sys.stderr)
        sys.exit(1)

    serializable_tags()

    Actor = namedtuple('Actor', ['name', 'consumes', 'produces', 'tags'])
    # Actor.name - vertex name
    # Actor.consumes - target vertex for directed edge
    # Actor.produces - source vertex for directed edge
    # Actor.tags - cluster
    actors = [Actor(name=actor.class_name,
                    consumes=tuple(c.serialize()['name'] for c in actor.consumes),
                    produces=tuple(p.serialize()['name'] for p in actor.produces),
                    tags=[elem for elem in tuple(t.serialize()['name'] for t in actor.tags) if elem != 'IPUWorkflowTag']
                    ) for actor in repository.actors]

    # mapping from tag to actors
    # key: tag, value: actor name
    tags = {}
    for actor in actors:
        for tag in actor.tags:
            if tag not in tags:
                tags[tag] = set()
            tags[tag].add(actor.name)

    # models that are consumed/produced by some actor
    models_consumed = set()
    models_produced = set()
    for actor in actors:
        models_consumed.update(actor.consumes)
        models_produced.update(actor.produces)

    # models which are produced/consumed but no actor consumes/produces them
    models_missing_consumer = models_produced.difference(models_consumed)
    models_missing_producer = models_consumed.difference(models_produced)

    # create dummy actors that consumes/produces models which lacks proper consumer/producer
    missing_consumer_actors = [Actor(name=model + 'Consumer',
                                    consumes=(model,),
                                    produces=(),
                                    tags=()
                                    ) for model in models_missing_consumer]
    missing_producer_actors = [Actor(name=model + 'Producer',
                                    consumes=(),
                                    produces=(model,),
                                    tags=()
                                    ) for model in models_missing_producer]

    actors.extend(missing_consumer_actors)
    actors.extend(missing_producer_actors)

    # mapping from consumed models to actors
    # key: consumed model, value: set of actor names that consumes the key
    model_consumers = {}
    for actor in actors:
        for model in actor.consumes:
            if model not in model_consumers:
                model_consumers[model] = set()
            model_consumers[model].add(actor.name)

    with open(args.dot, 'w') as file_handle:
        # opening tag
        file_handle.write('digraph g {\n')

        # basic directed graphs - only actors (nodes) and models (edges)
        basic_graph(actors, model_consumers, missing_producer_actors, missing_consumer_actors, file_handle)

        # set graph parameters
        node_distance(file_handle)

        # uncomment following line for clustering of actors by tags
        # warning: the edges are too close to each other, so it's usually hard to say
        # which label belongs to which edge
        if args.tags:
            clusters(tags, file_handle)

        # closing tag
        file_handle.write('}\n')

    print("To generate figure with graph, use dot tool:", file=sys.stderr)
    print("dot -Tpng -O {dot_file}".format(dot_file=args.dot), file=sys.stderr)
