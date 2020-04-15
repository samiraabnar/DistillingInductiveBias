import tensorflow as tf

class FFResnetBlock(tf.keras.layers.Layer):
  def __init__(self, filters, kernel_size, activation='relu',*inputs, **kwargs):
    super(FFResnetBlock, self).__init__(*inputs, **kwargs)
    self.filters = filters
    self.kernel_size = kernel_size
    self.activation = activation
    self.regularizer = tf.keras.regularizers.l1_l2(l1=0.00,
                                                   l2=0.000000002)

    self.create_layer()



  def create_layer(self):
    self.conv1 = tf.keras.layers.Dense(self.filters*9,
                                        activation=self.activation,
                                        kernel_regularizer=self.regularizer)
    self.batch_norm1 = tf.keras.layers.BatchNormalization()
    self.conv2 = tf.keras.layers.Dense(self.filters*9,
                                 activation=None,
                                 kernel_regularizer=self.regularizer)
    self.batch_norm2 = tf.keras.layers.BatchNormalization()
    self.add = tf.keras.layers.Add()
    self.activation = tf.keras.layers.Activation('relu')

  def call(self, inputs, training=None, **kwargs):
    outputs = self.conv1(inputs, training=training, **kwargs)
    outputs = self.batch_norm1(outputs,training=training, **kwargs)
    outputs = self.conv2(outputs, training=training, **kwargs)
    outputs = self.batch_norm2(outputs,training=training, **kwargs)
    outputs = self.add([outputs, inputs],training=training, **kwargs)
    outputs = self.activation(outputs, training=training, **kwargs)

    return outputs


class FFResnet(tf.keras.Model):
  def __init__(self, hparams, scope='ff_resnet', *inputs, **kwargs):
    if 'cl_token' in kwargs:
      del kwargs['cl_token']
    super(FFResnet, self).__init__(name=scope, *inputs, **kwargs)
    self.scope = scope
    self.hparams = hparams
    self.model_name = '_'.join([self.scope,
                                'h-' + str(self.hparams.hidden_dim),
                                'rd-' + str(self.hparams.num_res_net_blocks),
                                'hdrop-' + str(self.hparams.hidden_dropout_rate),
                                'indrop-' + str(self.hparams.input_dropout_rate)])

    self.regularizer = tf.keras.regularizers.l1_l2(l1=0.00,
                                                   l2=0.000000002)
    self.create_layers()
    self.rep_index = 1
    self.rep_layer = -1


  def create_layers(self):
    self.flat = tf.keras.layers.Flatten()
    self.batch_norm1 = tf.keras.layers.BatchNormalization()
    self.activation = tf.keras.layers.Activation('relu')


    self.conv1 = tf.keras.layers.Dense(self.hparams.filters[0]*9,
                                  activation=None,
                                  kernel_regularizer=self.regularizer)
    self.batch_norm2 = tf.keras.layers.BatchNormalization()
    self.conv2 = tf.keras.layers.Dense(self.hparams.filters[1]*9,
                                  activation=None,
                                  kernel_regularizer=self.regularizer)
    self.batch_norm3 = tf.keras.layers.BatchNormalization()

    self.resblocks = []
    for i in range(self.hparams.num_res_net_blocks):
      self.resblocks.append(FFResnetBlock(self.hparams.filters[2], self.hparams.kernel_size[2]))

    self.conv4 = tf.keras.layers.Dense(self.hparams.filters[3]*9,
                                        activation=None)
    self.batch_norm4 = tf.keras.layers.BatchNormalization()
    self.dense = tf.keras.layers.Dense(self.hparams.hidden_dim, activation='relu')
    self.dropout = tf.keras.layers.Dropout(self.hparams.hidden_dropout_rate)
    self.project = tf.keras.layers.Dense(self.hparams.output_dim, activation=None)

  def call(self, inputs, padding_symbol=None, training=None, **kwargs):
    x = self.flat(inputs, **kwargs)
    x = self.batch_norm1(x, training=training, **kwargs)

    x = self.conv1(x, training=training, **kwargs)
    x = self.batch_norm2(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)

    x = self.conv2(x, training=training, **kwargs)
    x = self.batch_norm3(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)

    for i in range(self.hparams.num_res_net_blocks):
      x = self.resblocks[i](x, training=training, **kwargs)
      x = self.dropout(x, training=training, **kwargs)

    x = self.conv4(x, training=training, **kwargs)
    x = self.batch_norm4(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)

    x = self.dense(x, training=training, **kwargs)
    x = self.dropout(x, training=training, **kwargs)
    outputs = self.project(x, training=training, **kwargs)

    return outputs

  def detailed_call(self, inputs, padding_symbol=None, training=None, **kwargs):
    self.layer_activations = []
    x = self.flat(inputs, **kwargs)

    x = self.batch_norm1(x, training=training, **kwargs)

    x = self.conv1(x, training=training, **kwargs)
    x = self.batch_norm2(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)

    self.layer_activations.append(x)

    x = self.conv2(x, training=training, **kwargs)
    x = self.batch_norm3(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)
    self.layer_activations.append(x)


    for i in range(self.hparams.num_res_net_blocks):
      x = self.resblocks[i](x, training=training, **kwargs)
      x = self.dropout(x, training=training, **kwargs)
      self.layer_activations.append(x)

    x = self.conv4(x, training=training, **kwargs)
    x = self.batch_norm4(x, training=training, **kwargs)
    x = self.activation(x)
    x = self.dropout(x, training=training, **kwargs)
    self.layer_activations.append(x)


    x = self.dense(x, training=training, **kwargs)
    x = self.dropout(x, training=training, **kwargs)
    self.layer_activations.append(x)
    pnltimt = x
    outputs = self.project(x, training=training, **kwargs)

    return outputs, pnltimt, self.layer_activations