import groovy.json.JsonSlurper

// The smithy-jar plugin asks for smithy-model/build/cli as the range [1.0, 2.0[. A range
// makes Gradle fetch maven-metadata.xml from Maven Central to list versions, on every run
// without a warm cache, and CI failed whenever Maven Central rate-limited it (HTTP 429).
// Forcing the version we compile against skips that lookup and stops the build tooling
// drifting to whatever 1.x is newest.
buildscript {
    configurations.classpath {
        resolutionStrategy.force(
            "software.amazon.smithy:smithy-model:1.69.0",
            "software.amazon.smithy:smithy-build:1.69.0",
            "software.amazon.smithy:smithy-cli:1.69.0",
        )
    }
}

plugins {
    java
    id("software.amazon.smithy.gradle.smithy-jar") version "1.3.0"
}

// Repositories are declared in settings.gradle.kts (Maven Central, or the CI pull-through cache).

dependencies {
    // Smithy core
    implementation("software.amazon.smithy:smithy-model:1.69.0")
    implementation("software.amazon.smithy:smithy-aws-traits:1.69.0")

    // OpenAPI projection (for API Gateway integration + docs)
    implementation("software.amazon.smithy:smithy-openapi:1.69.0")
    implementation("software.amazon.smithy:smithy-aws-apigateway-openapi:1.69.0")

    // Native TypeScript client codegen (published on Maven Central)
    smithyBuild("software.amazon.smithy.typescript:smithy-aws-typescript-codegen:0.49.1")
}

// Smithy's own validation happily accepts an operation that is defined but never
// listed in a service's `operations`. Nothing generates it: no client command, no
// OpenAPI path, no server binding. That is how P5 shipped GetMetricFamily /
// GetMetricReportManifest unreachable, and how the merge preview ended up with
// FindLinks / ListAnswerQualityRuns defined in their own files but referenced zero
// times from control-plane.smithy - git was clean and validate was green. Fail the
// build here instead of finding it in the UI.
//
// Reads the model smithyBuild already assembled for the projections, so the check
// sees exactly what the generators see. A dangling `use` (or an `operations` entry
// with no definition) is rejected by smithyBuild itself, before this task runs.
tasks.register("verifyOperationsMounted") {
    group = "verification"
    description = "Fails when an operation in src/main/smithy is not listed by any service."
    val modelJson = layout.buildDirectory.file("smithyprojections/models/source/model/model.json")
    dependsOn("smithyBuild")
    inputs.file(modelJson).withPropertyName("modelJson")
    doLast {
        @Suppress("UNCHECKED_CAST")
        val shapes = (JsonSlurper().parse(modelJson.get().asFile) as Map<String, Any?>)["shapes"]
            as Map<String, Map<String, Any?>>
        val operations = shapes.filterValues { it["type"] == "operation" }.keys
        // Shape references in the JSON AST are `{ target: "ns#Name" }`; accept bare
        // strings too so the check does not depend on that detail of the serializer.
        fun targets(list: Any?): List<String> = (list as? List<*>)?.map {
            ((it as? Map<*, *>)?.get("target") ?: it).toString()
        } ?: emptyList()
        val mounted = shapes.values
            .filter { it["type"] == "service" }
            .flatMap { targets(it["operations"]) }
            .toSet()
        val orphans = operations.filter { it !in mounted }.sorted()
        if (orphans.isNotEmpty()) {
            throw GradleException(
                "Operations defined but not listed in any service.operations: " +
                    orphans.joinToString(", ") +
                    ". Add them to the owning service in models/src/main/smithy."
            )
        }
        logger.lifecycle("verifyOperationsMounted: ${operations.size} operations, all mounted.")
    }
}

tasks.named("check") {
    dependsOn("verifyOperationsMounted")
}
