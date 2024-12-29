Network SHI {
Layer resnetv18_conv0_fwd {
Type: CONV
Dimensions { N: 1, C: 3, X: 224, Y: 224, K: 64, R: 7, S: 7 }
Dataflow {
TemporalMap(1 ,1:) K;
SpatialMap(4, 1) Y;
TemporalMap(56, 1) X;
TemporalMap(1, 1) C;
TemporalMap(7, 7) R;
TemporalMap(7, 7) S;
Cluster(4, P);
SpatialMap(56, 1) X;
}
}
}