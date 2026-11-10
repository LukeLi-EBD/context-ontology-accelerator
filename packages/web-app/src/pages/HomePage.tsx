// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Button,
  ColumnLayout,
  Container,
  ContentLayout,
  Grid,
  Header,
  Link,
  SpaceBetween,
} from "@cloudscape-design/components";
import { useUser } from "@auth";
import { useApiClient } from "@components";
import { useListNamespaces } from "../api-hooks/use-list-namespaces";
import { useToolsPanel } from "@components/ToolsPanelProvider";
import { HomeHelpPanel } from "./HomeHelpPanel";
import { ONBOARDING_ICON } from "@constants/drawer-icons";
import { useAppI18n } from "../i18n/LocaleProvider";
import type { AppMessage } from "../i18n/appMessages";

/**
 * Decorative ontology-graph watermark rendered behind the hero. Purely visual
 * (aria-hidden) and self-contained — it draws a small fixed graph of example
 * domain classes so the landing hero echoes the product's semantic model.
 */
const OntologyWatermark: React.FC = () => {
  const { t } = useAppI18n();
  const nodes: Array<{
    id: string;
    label: AppMessage;
    x: number;
    y: number;
    r: number;
  }> = [
    { id: "policy", label: "Policy", x: 520, y: 180, r: 34 },
    { id: "coverage", label: "Coverage", x: 700, y: 110, r: 26 },
    { id: "party", label: "Party", x: 640, y: 290, r: 28 },
    { id: "claim", label: "Claim", x: 820, y: 230, r: 30 },
    { id: "payment", label: "Payment", x: 940, y: 130, r: 22 },
    { id: "agent", label: "Agent", x: 760, y: 360, r: 20 },
    { id: "endorsement", label: "Endorsement", x: 440, y: 80, r: 20 },
  ];
  const edges: Array<[string, string]> = [
    ["policy", "coverage"],
    ["policy", "party"],
    ["policy", "endorsement"],
    ["claim", "policy"],
    ["claim", "party"],
    ["payment", "claim"],
    ["agent", "party"],
    ["agent", "policy"],
  ];
  const byId = new Map(nodes.map((n) => [n.id, n]));
  return (
    <div
      aria-hidden
      style={{
        position: "absolute",
        top: 0,
        bottom: "-20%",
        left: "calc(50% - 50vw)",
        right: "calc(50% - 50vw)",
        pointerEvents: "none",
        overflow: "hidden",
        opacity: 0.06,
        color: "currentColor",
      }}
    >
      <svg
        viewBox="0 0 1000 420"
        preserveAspectRatio="xMidYMid slice"
        style={{ width: "100%", height: "100%" }}
        fill="none"
        stroke="currentColor"
      >
        <g strokeWidth={1.5}>
          {edges.map(([a, b]) => {
            const na = byId.get(a);
            const nb = byId.get(b);
            if (!na || !nb) return null;
            return (
              <line key={`${a}-${b}`} x1={na.x} y1={na.y} x2={nb.x} y2={nb.y} />
            );
          })}
        </g>
        <g>
          {nodes.map((n) => (
            <g key={n.id}>
              <circle cx={n.x} cy={n.y} r={n.r} strokeWidth={2} />
              <circle cx={n.x} cy={n.y} r={3} fill="currentColor" />
              <text
                x={n.x + n.r + 8}
                y={n.y + 5}
                fill="currentColor"
                stroke="none"
                fontSize={14}
                fontFamily="inherit"
              >
                {t(n.label)}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

/** Subset of GET /system-health the home overview card needs (F01/F02). */
interface HomeOverview {
  status?: string;
  components?: Array<{ status: string }>;
  pointer?: { semver?: string | null; status?: string } | null;
  namedGraphs?: number | null;
}

/**
 * Context Ontology Accelerator landing / home page. This is the post-login destination (the OIDC
 * authenticate callback redirects to `/`). It welcomes the signed-in user and
 * routes them into the core workflow: create a namespace, then connect a
 * source, model an ontology, and serve it.
 */
export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const { registerDrawer, unregisterDrawer } = useToolsPanel();
  const { t } = useAppI18n();
  const greetingName = user?.name || user?.email || "";
  const namespaces = useListNamespaces();
  const namespaceCount =
    namespaces.data?.pages.reduce(
      (total, page) => total + (page.namespaces?.length ?? 0),
      0,
    ) ?? 0;
  // F03: an empty environment gets a next-step card instead of an empty page.
  const emptyEnvironment = namespaces.isSuccess && namespaceCount === 0;
  // F14: the overview card doubles as an entrance into an ontology page.
  const firstNamespaceId =
    namespaces.data?.pages[0]?.namespaces?.[0]?.namespaceId ?? null;

  // F01/F02: version pointer + named-graph count, refreshable without leaving `/`.
  const apiClient = useApiClient();
  const [overview, setOverview] = useState<HomeOverview | null>(null);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);

  const loadOverview = useCallback(async () => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      setOverview(await apiClient.get<HomeOverview>("/system-health"));
    } catch (e) {
      setOverview(null);
      setOverviewError(e instanceof Error ? e.message : "加载环境概览失败");
    } finally {
      setOverviewLoading(false);
    }
  }, [apiClient]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  const healthyComponents =
    overview?.components?.filter((c) => c.status === "ok").length ?? 0;
  const totalComponents = overview?.components?.length ?? 0;

  useEffect(() => {
    registerDrawer({
      id: "onboarding",
      content: <HomeHelpPanel />,
      trigger: { iconSvg: ONBOARDING_ICON },
      ariaLabels: {
        drawerName: t("Get started"),
        closeButton: t("Close Get started"),
      },
    });
    return () => unregisterDrawer("onboarding");
  }, [registerDrawer, unregisterDrawer, t]);

  return (
    <ContentLayout
      headerVariant="high-contrast"
      maxContentWidth={1000}
      header={
        <div style={{ position: "relative", overflow: "hidden" }}>
          <OntologyWatermark />
          <Box padding={{ vertical: "xxxl" }}>
            <Grid
              gridDefinition={[
                { colspan: { default: 12, s: 7 } },
                { colspan: { default: 12, s: 1 } },
                { colspan: { default: 12, s: 4 } },
              ]}
            >
              <SpaceBetween size="xs">
                <Box color="inherit" fontSize="body-m">
                  {t("AI Platform · Context Layer")}
                </Box>
                <Header variant="h1">
                  <Box
                    color="inherit"
                    fontSize="display-l"
                    fontWeight="heavy"
                    variant="span"
                  >
                    Context Ontology Accelerator
                  </Box>
                </Header>
                <Box fontWeight="light" fontSize="display-l" color="inherit">
                  {t("The governed context layer for enterprise AI.")}
                </Box>
                <Box variant="p" color="inherit" fontSize="heading-s">
                  {t(
                    "Connect to your Glue and SageMaker catalogs, induce a W3C-standard semantic model, and serve it to analysts and AI agents over MCP.",
                  )}
                </Box>
              </SpaceBetween>

              <div />

              <Container>
                <SpaceBetween size="l">
                  <Box variant="p">
                    {greetingName
                      ? `${t("Welcome, {name}.", { name: greetingName })} `
                      : ""}
                    {t(
                      "Create a namespace and connect your first source in a few guided steps.",
                    )}
                  </Box>
                  <SpaceBetween direction="horizontal" size="xs">
                    <Button
                      variant="primary"
                      onClick={() => navigate("/namespaces/create")}
                    >
                      {t("Get started")}
                    </Button>
                    <Button onClick={() => navigate("/namespaces")}>
                      {t("View namespaces")}
                    </Button>
                  </SpaceBetween>
                </SpaceBetween>
              </Container>
            </Grid>
          </Box>
        </div>
      }
    >
      <Container
        header={
          <Header
            variant="h2"
            description="版本指针、命名图计数、组件状态"
            actions={
              <Button
                iconName="refresh"
                onClick={loadOverview}
                loading={overviewLoading}
              >
                刷新
              </Button>
            }
          >
            环境概览
          </Header>
        }
      >
        {overviewError ? (
          <Box color="text-status-error">{overviewError}</Box>
        ) : (
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">T-Box 版本</Box>
              <Box>
                {overview?.pointer?.semver ?? "—"}
                {overview?.pointer?.status ? `（${overview.pointer.status}）` : ""}
              </Box>
            </div>
            <div>
              <Box variant="awsui-key-label">命名图</Box>
              <Box>{overview?.namedGraphs ?? "—"}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">组件</Box>
              <Box>
                {totalComponents > 0
                  ? `${healthyComponents}/${totalComponents} 正常`
                  : "—"}
              </Box>
            </div>
            <div data-testid="home-ontology-entry">
              <Box variant="awsui-key-label">本体入口</Box>
              {firstNamespaceId ? (
                <SpaceBetween size="xxs">
                  <Link href={`/namespaces/${firstNamespaceId}/ontology/graph`}>
                    浏览本体
                  </Link>
                  <Link href={`/namespaces/${firstNamespaceId}/ontology/canvas`}>
                    打开画布
                  </Link>
                </SpaceBetween>
              ) : (
                <Box color="text-body-secondary">—</Box>
              )}
            </div>
          </ColumnLayout>
        )}
      </Container>

      {emptyEnvironment && (
        <Container
          header={
            <Header
              variant="h2"
              description="当前没有任何命名空间，先按下面四步把一条数据走通。"
            >
              下一步
            </Header>
          }
        >
          <SpaceBetween size="l">
            <ColumnLayout columns={4} variant="text-grid">
              <SpaceBetween size="xs">
                <Header variant="h3">1. 建命名空间</Header>
                <Box variant="p" color="text-body-secondary">
                  给这批数据一个隔离的名字，后面的本体和文档都挂在它下面。
                </Box>
              </SpaceBetween>
              <SpaceBetween size="xs">
                <Header variant="h3">2. 导入本体</Header>
                <Box variant="p" color="text-body-secondary">
                  上传 T-Box，先把类、属性、必填约束定下来。
                </Box>
              </SpaceBetween>
              <SpaceBetween size="xs">
                <Header variant="h3">3. 上传文档</Header>
                <Box variant="p" color="text-body-secondary">
                  从文档抽实体，得到可点开的 A-Box 实例。
                </Box>
              </SpaceBetween>
              <SpaceBetween size="xs">
                <Header variant="h3">4. 去问答台验证</Header>
                <Box variant="p" color="text-body-secondary">
                  问一句，看召回、引用和来源对不对得上。
                </Box>
              </SpaceBetween>
            </ColumnLayout>
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="primary" onClick={() => navigate("/namespaces/create")}>
                建命名空间
              </Button>
              <Button onClick={() => navigate("/playground")}>先看问答台</Button>
            </SpaceBetween>
          </SpaceBetween>
        </Container>
      )}

      <Container header={<Header variant="h2">{t("How it works")}</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <SpaceBetween size="xs">
            <Header variant="h3">{t("Scan")}</Header>
            <Box variant="p" color="text-body-secondary">
              {t(
                "Point Context Ontology Accelerator at your Glue and SageMaker catalogs. It inventories tables and columns, then previews AI-generated business context for your review.",
              )}
            </Box>
          </SpaceBetween>
          <SpaceBetween size="xs">
            <Header variant="h3">{t("Ontology")}</Header>
            <Box variant="p" color="text-body-secondary">
              {t(
                "Draft a W3C-standard ontology over scanned catalogs. Author validation rules, define governed metrics, and publish through a versioned workflow.",
              )}
            </Box>
          </SpaceBetween>
          <SpaceBetween size="xs">
            <Header variant="h3">{t("Serve")}</Header>
            <Box variant="p" color="text-body-secondary">
              {t(
                "Expose the governed surface to analysts and agents. Every request flows through policy enforcement, with every decision logged.",
              )}
            </Box>
          </SpaceBetween>
        </ColumnLayout>
      </Container>
    </ContentLayout>
  );
};
