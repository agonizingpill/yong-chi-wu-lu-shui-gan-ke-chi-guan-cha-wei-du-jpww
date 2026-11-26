from hashlib import sha256
import json
import warnings

import numpy as np
from sklearn.decomposition import FactorAnalysis
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import StandardScaler

SEED = 1084
MIN_PRIMARY_LOADING = 0.45


class UnfitObservation(ValueError):
    pass


def identify_factors(items, surveys):
    numeric = []
    for survey in surveys:
        scores = {answer.item_id: answer.raw_value for answer in survey.marks}
        numeric.append([6 - scores[item.id] if item.reversed else scores[item.id] for item in items])
    data = np.asarray(numeric)
    if np.any(np.ptp(data, axis=0) == 0):
        raise UnfitObservation("有条目没有组内变化，无法拟合。请补采不同评分。")
    standardized = StandardScaler().fit_transform(data)
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always", ConvergenceWarning)
        factor = FactorAnalysis(n_components=2, rotation="varimax", random_state=SEED,
                                svd_method="lapack", max_iter=1000).fit(standardized)
    if any(issubclass(w.category, ConvergenceWarning) for w in seen):
        raise UnfitObservation("因子估计未收敛，不能据此修订观察表。")
    components = factor.components_.copy()
    for row in components:
        if row[np.argmax(abs(row))] < 0:
            row *= -1
    # Stable display order with the leading item first, independent of sign.
    components = np.asarray(sorted(components, key=lambda row: int(np.argmax(abs(row)))))
    details = []
    for i, (item, load) in enumerate(zip(items, components.T, strict=True)):
        main = int(np.argmax(abs(load))) + 1
        details.append({"item_id": item.id, "code": item.code, "reverse": item.reversed,
                        "loadings": [round(float(value), 4) for value in load],
                        "primary": main, "strong": bool(abs(load[main - 1]) >= MIN_PRIMARY_LOADING),
                        "communality": round(float(sum(load ** 2)), 4),
                        "residual": round(float(factor.noise_variance_[i]), 4)})
    return {"method": "FactorAnalysis / varimax", "dimensions": 2, "seed": SEED,
            "count": len(data), "iterations": int(factor.n_iter_),
            "log_likelihood": round(float(factor.loglike_[-1]), 4),
            "input_sha256": sha256(json.dumps(numeric, separators=(",", ":")).encode()).hexdigest(),
            "items": details}
