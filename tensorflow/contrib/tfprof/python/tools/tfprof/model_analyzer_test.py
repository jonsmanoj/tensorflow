# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from tensorflow.core.protobuf import config_pb2
from tensorflow.core.protobuf import rewriter_config_pb2
from tensorflow.python.client import session
from tensorflow.python.framework import ops
from tensorflow.python.ops import variables
from tensorflow.python.platform import gfile
from tensorflow.python.platform import test

# XXX: this depends on pywrap_tensorflow and must come later
from tensorflow.contrib.tfprof.python.tools.tfprof import model_analyzer
from tensorflow.contrib.tfprof.python.tools.tfprof.internal import model_analyzer_testlib as lib


class PrintModelAnalysisTest(test.TestCase):

  def testDumpToFile(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'dump')
    opts['output'] = 'file:outfile=' + outfile

    with session.Session() as sess:
      _ = lib.BuildSmallModel()
      model_analyzer.print_model_analysis(sess.graph, tfprof_options=opts)

      with gfile.Open(outfile, 'r') as f:
        self.assertEqual(u'node name | # parameters\n'
                         '_TFProfRoot (--/451 params)\n'
                         '  DW (3x3x3x6, 162/162 params)\n'
                         '  DW2 (2x2x6x12, 288/288 params)\n'
                         '  ScalarW (1, 1/1 params)\n',
                         f.read())

  def testSelectEverything(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'dump')
    opts['output'] = 'file:outfile=' + outfile
    opts['account_type_regexes'] = ['.*']
    opts['select'] = [
        'params', 'float_ops', 'occurrence', 'device', 'op_types',
        'input_shapes'
    ]

    rewriter_config = rewriter_config_pb2.RewriterConfig(
        disable_model_pruning=True)
    graph_options = config_pb2.GraphOptions(rewrite_options=rewriter_config)
    config = config_pb2.ConfigProto(graph_options=graph_options)
    with session.Session(config=config) as sess, ops.device('/cpu:0'):
      x = lib.BuildSmallModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(x,
                   options=config_pb2.RunOptions(
                       trace_level=config_pb2.RunOptions.FULL_TRACE),
                   run_metadata=run_meta)

      model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_options=opts)

      with gfile.Open(outfile, 'r') as f:
        # pylint: disable=line-too-long
        self.assertEqual(
            'node name | # parameters | # float_ops | assigned devices | op types | op count (run|defined) | input shapes\n_TFProfRoot (--/451 params, --/10.44k flops, _kTFScopeParent, --/7|--/35, )\n  Conv2D (0/0 params, 5.83k/5.83k flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|Conv2D, 1/1|1/1, 0:2x6x6x3|1:3x3x3x6)\n  Conv2D_1 (0/0 params, 4.61k/4.61k flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|Conv2D, 1/1|1/1, 0:2x3x3x6|1:2x2x6x12)\n  DW (3x3x3x6, 162/162 params, 0/0 flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|VariableV2|_trainable_variables, 1/2|1/10, )\n    DW/Assign (0/0 params, 0/0 flops, Assign, 0/0|1/1, 0:3x3x3x6|1:3x3x3x6)\n    DW/Initializer (0/0 params, 0/0 flops, _kTFScopeParent, 0/0|1/7, )\n      DW/Initializer/random_normal (0/0 params, 0/0 flops, Add, 0/0|1/6, 0:3x3x3x6|1:1)\n        DW/Initializer/random_normal/RandomStandardNormal (0/0 params, 0/0 flops, RandomStandardNormal, 0/0|1/1, 0:4)\n        DW/Initializer/random_normal/mean (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        DW/Initializer/random_normal/mul (0/0 params, 0/0 flops, Mul, 0/0|1/1, 0:3x3x3x6|1:1)\n        DW/Initializer/random_normal/shape (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        DW/Initializer/random_normal/stddev (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n    DW/read (0/0 params, 0/0 flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|Identity, 1/1|1/1, 0:3x3x3x6)\n  DW2 (2x2x6x12, 288/288 params, 0/0 flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|VariableV2|_trainable_variables, 1/2|1/10, )\n    DW2/Assign (0/0 params, 0/0 flops, Assign, 0/0|1/1, 0:2x2x6x12|1:2x2x6x12)\n    DW2/Initializer (0/0 params, 0/0 flops, _kTFScopeParent, 0/0|1/7, )\n      DW2/Initializer/random_normal (0/0 params, 0/0 flops, Add, 0/0|1/6, 0:2x2x6x12|1:1)\n        DW2/Initializer/random_normal/RandomStandardNormal (0/0 params, 0/0 flops, RandomStandardNormal, 0/0|1/1, 0:4)\n        DW2/Initializer/random_normal/mean (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        DW2/Initializer/random_normal/mul (0/0 params, 0/0 flops, Mul, 0/0|1/1, 0:2x2x6x12|1:1)\n        DW2/Initializer/random_normal/shape (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        DW2/Initializer/random_normal/stddev (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n    DW2/read (0/0 params, 0/0 flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|Identity, 1/1|1/1, 0:2x2x6x12)\n  ScalarW (1, 1/1 params, 0/0 flops, VariableV2|_trainable_variables, 0/0|1/10, )\n    ScalarW/Assign (0/0 params, 0/0 flops, Assign, 0/0|1/1, 0:1|1:1)\n    ScalarW/Initializer (0/0 params, 0/0 flops, _kTFScopeParent, 0/0|1/7, )\n      ScalarW/Initializer/random_normal (0/0 params, 0/0 flops, Add, 0/0|1/6, 0:1|1:1)\n        ScalarW/Initializer/random_normal/RandomStandardNormal (0/0 params, 0/0 flops, RandomStandardNormal, 0/0|1/1, 0:0)\n        ScalarW/Initializer/random_normal/mean (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        ScalarW/Initializer/random_normal/mul (0/0 params, 0/0 flops, Mul, 0/0|1/1, 0:1|1:1)\n        ScalarW/Initializer/random_normal/shape (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n        ScalarW/Initializer/random_normal/stddev (0/0 params, 0/0 flops, Const, 0/0|1/1, )\n    ScalarW/read (0/0 params, 0/0 flops, Identity, 0/0|1/1, 0:1)\n  init (0/0 params, 0/0 flops, NoOp, 0/0|1/1, 0:1|1:3x3x3x6|2:2x2x6x12)\n  zeros (0/0 params, 0/0 flops, /job:localhost/replica:0/task:0/cpu:0, /job:localhost/replica:0/task:0/cpu:0|Const, 1/1|1/1, )\n',
            f.read())
        # pylint: enable=line-too-long

  def testSimpleCodeView(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'dump')
    opts['output'] = 'file:outfile=' + outfile
    opts['account_type_regexes'] = ['.*']
    opts['show_name_regexes'] = ['.*model_analyzer_testlib.*']
    opts['account_displayed_op_only'] = False
    # TODO(xpan): Test 'micros'. Since the execution time changes each run,
    # it's a bit difficult to test it now.
    opts['select'] = [
        'bytes', 'params', 'float_ops', 'num_hidden_ops', 'device',
        'input_shapes'
    ]

    with session.Session() as sess:
      x = lib.BuildSmallModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(x,
                   options=config_pb2.RunOptions(
                       trace_level=config_pb2.RunOptions.FULL_TRACE),
                   run_metadata=run_meta)

      model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_cmd='code', tfprof_options=opts)

      with gfile.Open(outfile, 'r') as f:
        # pylint: disable=line-too-long
        self.assertEqual(
            'node name | output bytes | # parameters | # float_ops | assigned devices | input',
            f.read()[0:80])
        # pylint: enable=line-too-long

  def testComplexCodeView(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'dump')
    opts['output'] = 'file:outfile=' + outfile
    opts['account_type_regexes'] = ['.*']
    opts['show_name_regexes'] = ['.*model_analyzer_testlib.py.*']
    opts['account_displayed_op_only'] = False
    opts['select'] = ['params', 'float_ops']

    with session.Session() as sess:
      x = lib.BuildFullModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(x,
                   options=config_pb2.RunOptions(
                       trace_level=config_pb2.RunOptions.FULL_TRACE),
                   run_metadata=run_meta)

      tfprof_node = model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_cmd='code', tfprof_options=opts)

      # pylint: disable=line-too-long
      with gfile.Open(outfile, 'r') as f:
        lines = f.read().split('\n')
        result = '\n'.join([l[:min(len(l), 80)] for l in lines])
        self.assertEqual('node name | # parameters | # float_ops\n_TFProfRoot (--/2.84k params, --/91.04k flops)\n  model_analyzer_testlib.py:58:BuildFullModel:seq.append(array_... (0/1.80k para\n    model_analyzer_testlib.py:35:BuildSmallModel:image = array_ops... (0/0 param\n    model_analyzer_testlib.py:39:BuildSmallModel:initializer=init_... (0/4 param\n    model_analyzer_testlib.py:43:BuildSmallModel:initializer=init_... (0/648 par\n    model_analyzer_testlib.py:44:BuildSmallModel:x = nn_ops.conv2d... (0/0 param\n    model_analyzer_testlib.py:48:BuildSmallModel:initializer=init_... (0/1.15k p\n    model_analyzer_testlib.py:49:BuildSmallModel:x = nn_ops.conv2d... (0/0 param\n  model_analyzer_testlib.py:62:BuildFullModel:cell, array_ops.c... (0/1.04k para\n  model_analyzer_testlib.py:64:BuildFullModel:target = array_op... (0/0 params, \n  model_analyzer_testlib.py:65:BuildFullModel:loss = nn_ops.l2_... (0/0 params, \n  model_analyzer_testlib.py:67:BuildFullModel:return sgd_op.min... (0/0 params, \n',
                         result)

      self.assertLess(0, tfprof_node.total_exec_micros)
      self.assertEqual(2844, tfprof_node.total_parameters)
      self.assertEqual(91040, tfprof_node.total_float_ops)
      self.assertEqual(5, len(tfprof_node.children))
      self.assertEqual('_TFProfRoot', tfprof_node.name)
      self.assertEqual(
          'model_analyzer_testlib.py:58:BuildFullModel:seq.append(array_...',
          tfprof_node.children[0].name)
      self.assertEqual(
          'model_analyzer_testlib.py:62:BuildFullModel:cell, array_ops.c...',
          tfprof_node.children[1].name)
      self.assertEqual(
          'model_analyzer_testlib.py:64:BuildFullModel:target = array_op...',
          tfprof_node.children[2].name)
      self.assertEqual(
          'model_analyzer_testlib.py:65:BuildFullModel:loss = nn_ops.l2_...',
          tfprof_node.children[3].name)
      self.assertEqual(
          'model_analyzer_testlib.py:67:BuildFullModel:return sgd_op.min...',
          tfprof_node.children[4].name)
      # pylint: enable=line-too-long

  def testCodeViewLeafGraphNode(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    opts['account_type_regexes'] = ['.*']
    opts['account_displayed_op_only'] = False
    opts['select'] = [
        'bytes', 'params', 'float_ops', 'device'
    ]
    opts['output'] = 'none'

    with session.Session() as sess:
      x = lib.BuildSmallModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(x,
                   options=config_pb2.RunOptions(
                       trace_level=config_pb2.RunOptions.FULL_TRACE),
                   run_metadata=run_meta)

      tfprof_node = model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_cmd='code', tfprof_options=opts)

      leaf = tfprof_node
      while leaf.children:
        self.assertEqual(0, len(leaf.graph_nodes))
        leaf = leaf.children[0]
      self.assertEqual(1, len(leaf.graph_nodes))

  def testTimeline(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'timeline')
    opts['output'] = 'timeline:outfile=' + outfile
    opts['account_type_regexes'] = ['.*']
    opts['max_depth'] = 100000
    opts['step'] = 0

    with session.Session() as sess:
      x = lib.BuildFullModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(
          x,
          options=config_pb2.RunOptions(
              trace_level=config_pb2.RunOptions.FULL_TRACE),
          run_metadata=run_meta)

      _ = model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_cmd='graph', tfprof_options=opts)

      with gfile.Open(outfile, 'r') as f:
        # Test that a json file is created.
        # TODO(xpan): tfprof Timeline isn't quite correct on Windows.
        # Investigate why.
        if os.name != 'nt':
          self.assertLess(1000, len(f.read()))
        else:
          self.assertLess(1, len(f.read()))

  def testOpView(self):
    ops.reset_default_graph()
    opts = model_analyzer.TRAINABLE_VARS_PARAMS_STAT_OPTIONS.copy()
    outfile = os.path.join(test.get_temp_dir(), 'dump')
    opts['output'] = 'file:outfile=' + outfile
    opts['account_type_regexes'] = ['.*']
    opts['min_occurrence'] = 10
    opts['select'] = ['params', 'micros', 'occurrence', 'input_shapes']
    opts['order_by'] = 'occurrence'

    with session.Session() as sess:
      x = lib.BuildFullModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(x,
                   options=config_pb2.RunOptions(
                       trace_level=config_pb2.RunOptions.FULL_TRACE),
                   run_metadata=run_meta)

      tfprof_node = model_analyzer.print_model_analysis(
          sess.graph, run_meta, tfprof_cmd='op', tfprof_options=opts)

      with gfile.Open(outfile, 'r') as f:
        # pylint: disable=line-too-long
        self.assertEqual(
            'nodename|totalexecutiontime|acceleratorexecutiontime|cpuexecutiontime|#parameters|opoccurrence(run|defined)|inputshapes\n',
            f.read().replace('\t', '').replace(' ', '')[0:120])
        # pylint: enable=line-too-long

      total_children = 0
      last_occurrence = 1e32
      input_shapes = 0
      last_total_micros = tfprof_node.total_exec_micros
      last_micros = tfprof_node.exec_micros
      while tfprof_node.children:
        for gnode in tfprof_node.graph_nodes:
          input_shapes += len(gnode.input_shapes)
        self.assertEqual(len(tfprof_node.children), 1)
        tfprof_node = tfprof_node.children[0]

        self.assertEqual(
            last_total_micros, tfprof_node.total_exec_micros + last_micros)
        last_total_micros = tfprof_node.total_exec_micros
        last_micros = tfprof_node.exec_micros

        total_children += 1
        self.assertLessEqual(len(tfprof_node.graph_nodes), last_occurrence)
        last_occurrence = len(tfprof_node.graph_nodes)

      self.assertEqual(total_children, 15)
      self.assertGreater(input_shapes, 0)

  def testAdvisor(self):
    ops.reset_default_graph()

    with session.Session() as sess:
      x = lib.BuildFullModel()

      sess.run(variables.global_variables_initializer())
      run_meta = config_pb2.RunMetadata()
      _ = sess.run(
          x,
          options=config_pb2.RunOptions(
              trace_level=config_pb2.RunOptions.FULL_TRACE),
          run_metadata=run_meta)

      advice_pb = model_analyzer.advise(sess.graph, run_meta)
      self.assertTrue('AcceleratorUtilizationChecker' in advice_pb.checkers)
      self.assertTrue('ExpensiveOperationChecker' in advice_pb.checkers)
      self.assertTrue('OperationChecker' in advice_pb.checkers)

      checker = advice_pb.checkers['AcceleratorUtilizationChecker']
      if test.is_gpu_available():
        self.assertGreater(len(checker.reports), 0)
      else:
        self.assertEqual(len(checker.reports), 0)
      checker = advice_pb.checkers['ExpensiveOperationChecker']
      self.assertGreater(len(checker.reports), 0)


if __name__ == '__main__':
  test.main()
