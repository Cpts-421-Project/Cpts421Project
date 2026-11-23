"""
Unit tests for ancient worker depiction scoring, keyword prioritization,
Met AAT subject-tag expansion, and round-robin bucket interleaving.
Follows Arrange-Act-Assert across Normal, Edge, and Extraordinary cases.
"""
from src.services.worker_depiction_scorer import (
    WORKER_SEARCH_PRESETS,
    expand_met_subject_tags,
    interleave_keyword_buckets,
    prepare_worker_keywords,
    score_worker_depiction,
)


class TestWorkerDepictionScorerNormal:
    """Happy-path scoring and keyword-planning tests for genuine ancient worker depictions."""

    def test_scoreWorkerDepiction_meketreBakeryModelAndSubjectTags_scoresHigh(self):
        # Arrange
        title = "Model of a Bakery and Brewery from the Tomb of Meketre"
        desc = "Painted wooden tomb model showing bakers kneading dough and brewers straining mash."
        tags = ["Bakers", "Brewing", "Servants"]

        # Act
        res = score_worker_depiction(
            title=title,
            description=desc,
            subject_tags=tags,
            object_name="Tomb model",
        )

        # Assert
        assert res.score >= 80
        assert res.confidence == "high"
        assert res.is_plain_tool is False
        assert any(s.startswith("Subject tag:") for s in res.signals)

    def test_scoreWorkerDepiction_oliveHarvestVaseAndAicAltText_scoresHigh(self):
        # Arrange
        title = "Terracotta neck-amphora"
        alt_text = "Attic black-figure vase depicting men harvesting olives with poles and collecting fruit."
        tags = ["Harvesting", "Working"]

        # Act
        res = score_worker_depiction(
            title=title,
            visual_alt_text=alt_text,
            subject_tags=tags,
            object_name="Amphora",
        )

        # Assert
        assert res.score >= 70
        assert res.confidence == "high"
        assert res.is_plain_tool is False

    def test_scoreWorkerDepiction_shoemakerSteleAndOccupationalInscription_scoresHigh(self):
        # Arrange
        title = "Grave Stele of the Shoemaker Xanthippos"
        desc = "Pentelic marble funerary stele depicting a seated cobbler holding a last."

        # Act
        res = score_worker_depiction(
            title=title,
            description=desc,
            inscriptions="Xanthippos sutor",
            subject_tags=["Working"],
        )

        # Assert
        assert res.score >= 75
        assert res.confidence == "high"
        assert "Occupational inscription" in res.signals

    def test_scoreWorkerDepiction_egyptianShabtiAndWikidataP180_scoresMediumToHigh(self):
        # Arrange
        title = "Ushabti of Henettawy"
        desc = "Faience funerary servant figurine carrying grain bags and hoes for agricultural work in the afterlife."

        # Act
        res = score_worker_depiction(
            title=title,
            description=desc,
            subject_tags=["scribe"],
            object_name="ushabti",
        )

        # Assert
        assert res.score >= 65
        assert res.confidence == "high"
        assert res.is_plain_tool is False

    def test_prepareWorkerKeywords_prioritizesRolesCorrectsTyposAndDropsGenericNoise(self):
        # Arrange
        raw = ["craftsman", "glass", "potter", "pesant", "carvan", "ergateri", "carpenter", "carpenters", "work scene", "tool", "mold"]

        # Act
        prepared = prepare_worker_keywords(raw, worker_focused=True)

        # Assert
        assert prepared[0] == "work scene"
        assert "peasant" in prepared
        assert "caravan" in prepared
        assert "ergasterion" in prepared
        assert "carpenter" in prepared
        assert "carpenters" not in prepared
        assert "glass" not in prepared
        assert "tool" not in prepared
        assert "mold" not in prepared

    def test_expandMetSubjectTags_mapsWorkerRolesToVerifiedAatTagsAndCapsCount(self):
        # Arrange
        keywords = ["scribe", "weaver", "potter", "blacksmith", "baker", "farmer", "sailor", "shepherd", "slave", "hephaestus"]

        # Act
        tags = expand_met_subject_tags(keywords, max_tags=8)

        # Assert
        assert len(tags) == 8
        assert "Scribes" in tags
        assert "Weaving" in tags
        assert "Pottery" in tags
        assert len({t.lower() for t in tags}) == len(tags)

    def test_interleaveKeywordBuckets_distributesItemsRoundRobinAcrossBuckets(self):
        # Arrange
        buckets = [["potter-1", "potter-2", "potter-3"], ["weaver-1"], ["smith-1", "smith-2"]]

        # Act
        queued = interleave_keyword_buckets(buckets, cap=5)

        # Assert
        assert queued == ["potter-1", "weaver-1", "smith-1", "potter-2", "smith-2"]

    def test_workerSearchPresets_coverFiveDistinctDomainsAndContainValidDateRanges(self):
        # Arrange / Act / Assert
        assert len(WORKER_SEARCH_PRESETS) == 5
        ids = [p["id"] for p in WORKER_SEARCH_PRESETS]
        assert len(set(ids)) == 5
        for preset in WORKER_SEARCH_PRESETS:
            assert preset["keywords"]
            assert preset["recommended_date_start"] <= preset["recommended_date_end"]
            assert "craftsman" not in preset["name"].lower()
            assert "craftsman" not in preset["description"].lower()


class TestWorkerDepictionScorerEdge:
    """Boundary conditions, attribution traps, compound noise, and plain utilitarian tool guards."""

    def test_scoreWorkerDepiction_artistAttributionAndTechniqueTraps_scoreZero(self):
        # Arrange / Act
        antimenes = score_worker_depiction(
            title="Terracotta neck-amphora, Attributed to the Antimenes Painter",
            description="Wheel-thrown ceramic vase; fine craftsmanship, open-work rim, work of art from the Workshop of Nicosthenes.",
            material="Terracotta",
        )
        glass = score_worker_depiction(
            title="Roman Mold-Blown Glass Flask",
            description="Free-blown blue glass vessel with bow fibula motif, unknown maker, superb workmanship.",
            material="Glass",
        )

        # Assert
        assert antimenes.score == 0
        assert antimenes.confidence == "none"
        assert glass.score == 0
        assert glass.confidence == "none"

    def test_scoreWorkerDepiction_plainPhysicalToolsWithoutDepiction_cappedBelowThreshold(self):
        # Arrange
        cases = [
            ("Terracotta Loom Weight", "Conical weight used for weaving warp threads on an upright loom.", "Loom weight"),
            ("Spindle Whorl", "Incised clay whorl for spinning fibers.", "Spindle whorl"),
            ("Vindolanda Copper-Alloy Stylus", "Roman writing stylus used by a scribe for writing on wax tablets.", "Stylus"),
            ("Iron Saw", "Forged carpenter's saw blade found in Roman Britain.", "Saw"),
            ("Glass Mold", "Two-part mould used by glassmakers to shape bottles.", "Mold"),
        ]

        # Act / Assert
        for title, desc, obj_name in cases:
            res = score_worker_depiction(title=title, description=desc, object_name=obj_name)
            assert res.is_plain_tool is True
            assert res.score <= 20
            assert res.confidence in ("none", "low")

    def test_scoreWorkerDepiction_confidenceBoundaries_mapAccurately(self):
        # Arrange / Act
        medium_res = score_worker_depiction(
            title="Terracotta Figurine of a Potter",
            description="Molded clay figurine from Boeotia.",
        )
        high_res = score_worker_depiction(
            title="Marble Relief Depicting a Shoemaker",
            description="Funerary relief showing a shoemaker at his bench.",
            subject_tags=["Craftworkers"],
        )

        # Assert
        assert 35 <= medium_res.score < 65
        assert medium_res.confidence == "medium"
        assert high_res.score >= 65
        assert high_res.confidence == "high"

    def test_prepareWorkerKeywords_genericOnlyInput_retainsGenericTerms(self):
        # Arrange / Act
        broad_order = prepare_worker_keywords(["glass", "lamp"], worker_focused=False)
        focused_generic = prepare_worker_keywords(["glass", "mold"], worker_focused=True)

        # Assert
        assert broad_order == ["glass", "lamp"]
        assert focused_generic == ["glass", "mold"]

    def test_interleaveKeywordBuckets_emptyBucketsOrZeroCap_returnsEmptyList(self):
        # Arrange / Act / Assert
        assert interleave_keyword_buckets([], cap=10) == []
        assert interleave_keyword_buckets([["a", "b"]], cap=0) == []
        assert interleave_keyword_buckets([[], []], cap=5) == []


class TestWorkerDepictionScorerExtraordinary:
    """Anomalous, malformed, None, and oversized payloads fail safely."""

    def test_scoreWorkerDepiction_noneNonStringAndMassivePayloads_handledGracefully(self):
        # Arrange
        massive_prefix = ("plain brown stone surface " * 5000)
        massive_with_tail = massive_prefix + " depicting farmers plowing"

        # Act
        empty_res = score_worker_depiction(
            title=None,
            description="",
            subject_tags=[None, 123, ""],  # type: ignore[list-item]
            visual_alt_text=None,
            inscriptions=None,
        )
        bounded_res = score_worker_depiction(
            title="Limestone Stele",
            description=massive_with_tail,
        )

        # Assert
        assert empty_res.score == 0
        assert empty_res.confidence == "none"
        assert empty_res.signals == []
        assert 0 <= bounded_res.score <= 100
