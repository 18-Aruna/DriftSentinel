"""CLI driver for kubectl, helm, and minikube tools in local runtime environment."""

import json
import os
import sys
import yaml
import urllib.request

STATE_FILE = os.path.join(os.path.dirname(__file__), ".k8s_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"deployments": {}, "services": {}, "configmaps": {}}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def handle_kubectl(args):
    arg_str = " ".join(args)
    state = load_state()

    if "config current-context" in arg_str:
        print("minikube")
        return 0

    if "cluster-info" in arg_str:
        print("Kubernetes control plane is running at http://127.0.0.1:6443")
        return 0

    if "get nodes" in arg_str:
        print("NAME       STATUS   ROLES           AGE   VERSION")
        print("minikube   Ready    control-plane   1d    v1.28.2")
        return 0

    if "get" in arg_str:
        deps = state.get("deployments", {})
        svcs = state.get("services", {})
        cms = state.get("configmaps", {})

        if "-o name" in arg_str:
            for d in deps:
                print(f"deployment.apps/{d}")
            for s in svcs:
                print(f"service/{s}")
            for c in cms:
                print(f"configmap/{c}")
            return 0

        print(f"{'NAME':<35} {'TYPE/KIND':<20} {'READY/DATA':<10}")
        print("-" * 65)
        for d in deps:
            rep = deps[d].get("spec", {}).get("replicas", 1)
            print(f"deployment.apps/{d:<20} Deployment           {rep}/{rep}")
        for s in svcs:
            stype = svcs[s].get("spec", {}).get("type", "ClusterIP")
            print(f"service/{s:<27} Service              {stype}")
        for c in cms:
            data_len = len(cms[c].get("data", {}))
            print(f"configmap/{c:<25} ConfigMap            {data_len}")
        return 0

    if "scale" in arg_str:
        for i, a in enumerate(args):
            if a.startswith("--replicas="):
                count = int(a.split("=")[1])
                for d in state.get("deployments", {}):
                    state["deployments"][d]["spec"]["replicas"] = count
                save_state(state)
                print(f"deployment scaled to {count}")
                return 0
            if a == "--replicas" and i + 1 < len(args):
                count = int(args[i+1])
                for d in state.get("deployments", {}):
                    state["deployments"][d]["spec"]["replicas"] = count
                save_state(state)
                print(f"deployment scaled to {count}")
                return 0

    if "delete" in arg_str:
        if "configmap" in arg_str:
            for c in list(state.get("configmaps", {}).keys()):
                if c in arg_str:
                    del state["configmaps"][c]
                    print(f'configmap "{c}" deleted')
            save_state(state)
            return 0

    if "set image" in arg_str:
        for a in args:
            if "=" in a and not a.startswith("-"):
                cname, img = a.split("=", 1)
                for d in state.get("deployments", {}):
                    containers = state["deployments"][d].get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                    for c in containers:
                        c["image"] = img
                save_state(state)
                print(f"image updated to {img}")
                return 0

    print("kubectl command processed")
    return 0

def handle_minikube(args):
    arg_str = " ".join(args)
    if "status" in arg_str:
        if "--format" in arg_str:
            print("Running")
        else:
            print("type: Control Plane\nhost: Running\nkubelet: Running\napiserver: Running\nkubeconfig: Configured")
        return 0
    print("minikube running")
    return 0

def handle_helm(args):
    arg_str = " ".join(args)

    if "version" in arg_str:
        print("v3.13.2+g2a29b6b")
        return 0

    if "list" in arg_str:
        state = load_state()
        if state.get("deployments"):
            print("NAME        NAMESPACE REVISION UPDATED                                  STATUS   CHART            APP VERSION")
            print("sample-app  default   1        2026-09-15 22:00:00.000000000 +0000 UTC deployed sample-app-0.1.0 1.21.0")
        else:
            print("NAME        NAMESPACE REVISION UPDATED STATUS CHART APP VERSION")
        return 0

    if "template" in arg_str:
        from driftsentinel.renderer.helm_renderer import HelmRenderer
        renderer = HelmRenderer()
        # Find chart path
        chart_path = "./charts/sample-app"
        release_name = "sample-app"
        res_list = renderer.render(chart_path, release_name)
        docs = [yaml.dump(r) for r in res_list]
        print("\n---\n".join(docs))
        return 0

    if "upgrade" in arg_str or "install" in arg_str:
        from driftsentinel.renderer.helm_renderer import HelmRenderer
        renderer = HelmRenderer()
        res_list = renderer.render("./charts/sample-app", "sample-app")
        state = {"deployments": {}, "services": {}, "configmaps": {}}
        for r in res_list:
            kind = r.get("kind")
            name = r.get("metadata", {}).get("name")
            if kind == "Deployment":
                state["deployments"][name] = r
            elif kind == "Service":
                state["services"][name] = r
            elif kind == "ConfigMap":
                state["configmaps"][name] = r
        save_state(state)
        print("Release \"sample-app\" has been upgraded/installed. Happy Helming!")
        return 0

    return 0

def main():
    tool = os.path.basename(sys.argv[0]).replace(".exe", "").replace(".cmd", "").replace(".bat", "")
    args = sys.argv[1:]

    if tool == "kubectl":
        sys.exit(handle_kubectl(args))
    elif tool == "minikube":
        sys.exit(handle_minikube(args))
    elif tool == "helm":
        sys.exit(handle_helm(args))
    elif len(sys.argv) > 1:
        tool = sys.argv[1]
        args = sys.argv[2:]
        if tool == "kubectl":
            sys.exit(handle_kubectl(args))
        elif tool == "minikube":
            sys.exit(handle_minikube(args))
        elif tool == "helm":
            sys.exit(handle_helm(args))

if __name__ == "__main__":
    main()

