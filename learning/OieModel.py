__author__ = 'diego'


import theano.tensor as T
import theano
from models.encoders.RelationClassifier import IndependentRelationClassifiers

class OieModelFunctions(object):

    def __init__(self, rng, featureDim, embedSize, relationNum, argVocSize, model,
                  data, extEmb, extendedReg, alpha):
        """
        :param rng: RandomState
        :param featureDim:
        :param embedSize:
        :param relationNum:
        :param argVocSize: int - entity number
        :param model: str - "A" "C" or "AC"
        :param data: DatasetManager
        :param extEmb: bool external embeddings
        :param extendedReg:
        :param alpha:
        """
        self.rng = rng

        self.h = featureDim
        self.k = embedSize
        self.r = relationNum

        self.a = argVocSize
        self.model = model
        self.relationClassifiers = IndependentRelationClassifiers(rng, featureDim, relationNum)
        self.params = self.relationClassifiers.params # list of theano.shared()
        self.alpha = alpha
        print 'Feature space size =', self.h
        print 'Argument vocabulary size =', argVocSize

        self.L1 = T.sum(abs(self.relationClassifiers.W))

        self.L2 = T.sum(T.sqr(self.relationClassifiers.W))  # + T.sum(T.sqr(self.relationClassifiers.Wb))

        if self.model == 'A':
            print 'Bilinear Model'
            from models.decoders.Bilinear import Bilinear

            self.argProjector = Bilinear(rng, embedSize, relationNum, self.a, data, extEmb) # decoder
            self.params += self.argProjector.params
            if extendedReg:
                self.L1 += T.sum(abs(self.argProjector.C))
                self.L2 += T.sum(T.sqr(self.argProjector.C))

        elif self.model == 'AC':
            print 'Bilinear + Selectional Preferences Model'
            from models.decoders.BilinearPlusSP import BilinearPlusSP

            self.argProjector = BilinearPlusSP(rng, embedSize, relationNum, self.a, data, extEmb)
            self.params += self.argProjector.params
            if extendedReg:
                self.L1 += T.sum(abs(self.argProjector.C1)) + T.sum(abs(self.argProjector.C2)) + T.sum(abs(self.argProjector.C))
                self.L2 += T.sum(T.sqr(self.argProjector.C1)) + T.sum(T.sqr(self.argProjector.C2)) + T.sum(T.sqr(self.argProjector.C))


        elif self.model == 'C':
            print 'Selectional Preferences'
            from models.decoders.SelectionalPreferences import SelectionalPreferences

            self.argProjector = SelectionalPreferences(rng, embedSize, relationNum, self.a, data, extEmb)
            self.params += self.argProjector.params
            if extendedReg:
                self.L1 += T.sum(abs(self.argProjector.C1)) + T.sum(abs(self.argProjector.C2))
                self.L2 += T.sum(T.sqr(self.argProjector.C1)) + T.sum(T.sqr(self.argProjector.C2))



    def buildTrainErrComputation(self, batchSize, negNum, xFeats, args1, args2, neg1, neg2):
        l = batchSize
        n = negNum

        # print xFeats
        print "Relation classifiers..."
        # relationLabeler.output are probabilities of relations assignment arranged in a tensor [l, r]
        relationProbs = self.relationClassifiers.compRelationProbsFunc(xFeats=xFeats)
        print "Arg projection..."

        # why two entropys?
        entropy = self.alpha * -T.sum(T.log(relationProbs) * relationProbs, axis=1)  # [l,r] * [l,r] = [l]

        # isn't it all the same?
        if self.model == 'A':
            allScores = self.argProjector.getScores(args1, args2, l, n, relationProbs, neg1, neg2, entropy)


        elif self.model == 'AC':
            allScores = self.argProjector.getScores(args1, args2, l, n, relationProbs, neg1, neg2, entropy)


        elif self.model == 'C':
            allScores = self.argProjector.getScores(args1, args2, l, n, relationProbs, neg1, neg2, entropy)


        resError = -T.mean(allScores)
        print "Done with building the graph..."
        # resError = theano.printing.Print("resError ")(resError)
        return resError, entropy, relationProbs, allScores




    def buildLabelComputation(self, batchSize, xFeats):
        """
        :param batchsize:
        :param xFeats:
        :return:(labels, relationProbs), ([l],[l, r])
        """
        #  xFeats [ l * e, h ] matrix
        return self.relationClassifiers.labelFunct(batchSize, xFeats)


    def buildRelationProbComputation(self, batchSize, xFeats):
        return self.relationClassifiers.compRelationProbsFunc(xFeats)


