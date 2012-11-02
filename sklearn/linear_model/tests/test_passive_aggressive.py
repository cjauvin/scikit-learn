import numpy as np
import scipy.sparse as sp

from sklearn.utils.testing import assert_less
from sklearn.utils.testing import assert_greater
from sklearn.utils.testing import assert_array_almost_equal
from sklearn.utils.testing import assert_raises

from sklearn.base import ClassifierMixin
from sklearn.utils import check_random_state
from sklearn.datasets import load_iris
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.linear_model import PassiveAggressiveRegressor

iris = load_iris()
random_state = check_random_state(12)
indices = np.arange(iris.data.shape[0])
random_state.shuffle(indices)
X = iris.data[indices]
y = iris.target[indices]
X_csr = sp.csr_matrix(X)


class MyPassiveAggressive(ClassifierMixin):

    def __init__(self, C=1.0, epsilon=0.01, loss="hinge",
                 fit_intercept=True, n_iter=1, random_state=None):
        self.C = C
        self.epsilon = epsilon
        self.loss = loss
        self.fit_intercept = fit_intercept
        self.n_iter = n_iter

    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.w = np.zeros(n_features, dtype=np.float64)
        self.b = 0.0

        for t in range(self.n_iter):
            for i in range(n_samples):
                p = self.project(X[i])
                if self.loss in ("hinge", "squared_hinge"):
                    loss = max(1 - y[i] * p, 0)
                else:
                    loss = max(np.abs(p - y[i]) - self.epsilon, 0)

                sqnorm = np.dot(X[i], X[i])

                if self.loss in ("hinge", "epsilon_insensitive"):
                    step = min(self.C, loss / sqnorm)
                elif self.loss in ("squared_hinge",
                                   "squared_epsilon_insensitive"):
                    step = loss / (sqnorm + 1.0 / (2 * self.C))

                if self.loss in ("hinge", "squared_hinge"):
                    step *= y[i]
                else:
                    step *= np.sign(y[i] - p)


                self.w += step * X[i]
                if self.fit_intercept:
                    self.b += step

    def project(self, X):
        return np.dot(X, self.w) + self.b


def test_classifier_accuracy():
    for data in (X, X_csr):
        for fit_intercept in (True, False):
            clf = PassiveAggressiveClassifier(C=1.0, n_iter=30,
                                              fit_intercept=fit_intercept,
                                              random_state=0)
            clf.fit(data, y)
            score = clf.score(data, y)
            assert_greater(score, 0.79)


def test_classifier_partial_fit():
    classes = np.unique(y)
    for data in (X, X_csr):
            clf = PassiveAggressiveClassifier(C=1.0,
                                              fit_intercept=True,
                                              random_state=0)
            for t in xrange(30):
                clf.partial_fit(data, y, classes)
            score = clf.score(data, y)
            assert_greater(score, 0.79)


def test_classifier_correctness():
    y_bin = y.copy()
    y_bin[y != 1] = -1

    for loss in ("hinge", "squared_hinge"):

        clf1 = MyPassiveAggressive(C=1.0,
                                   loss=loss,
                                   fit_intercept=True,
                                   n_iter=2)
        clf1.fit(X, y_bin)

        clf2 = PassiveAggressiveClassifier(C=1.0,
                                           loss=loss,
                                           fit_intercept=True,
                                           n_iter=2)
        clf2.fit(X, y_bin)

        assert_array_almost_equal(clf1.w, clf2.coef_.ravel())


def test_predict_proba_undefined():
    clf = PassiveAggressiveClassifier()
    for meth in ("predict_proba", "predict_log_proba"):
        assert_raises(AttributeError, lambda x: getattr(clf, x), meth)


def test_regressor_mse():
    y_bin = y.copy()
    y_bin[y != 1] = -1

    for data in (X, X_csr):
        for fit_intercept in (True, False):
            reg = PassiveAggressiveRegressor(C=1.0, n_iter=50,
                                             fit_intercept=fit_intercept,
                                             random_state=0)
            reg.fit(data, y_bin)
            pred = reg.predict(data)
            assert_less(np.mean((pred - y_bin) ** 2), 1.7)


def test_regressor_partial_fit():
    y_bin = y.copy()
    y_bin[y != 1] = -1

    for data in (X, X_csr):
            reg = PassiveAggressiveRegressor(C=1.0,
                                             fit_intercept=True,
                                             random_state=0)
            for t in xrange(50):
                reg.partial_fit(data, y_bin)
            pred = reg.predict(data)
            assert_less(np.mean((pred - y_bin) ** 2), 1.7)


def test_regressor_correctness():
    y_bin = y.copy()
    y_bin[y != 1] = -1

    for loss in ("epsilon_insensitive", "squared_epsilon_insensitive"):
        reg1 = MyPassiveAggressive(C=1.0,
                                   loss=loss,
                                   fit_intercept=True,
                                   n_iter=2)
        reg1.fit(X, y_bin)

        reg2 = PassiveAggressiveRegressor(C=1.0,
                                          loss=loss,
                                          fit_intercept=True,
                                          n_iter=2)
        reg2.fit(X, y_bin)

        assert_array_almost_equal(reg1.w, reg2.coef_.ravel(), decimal=2)