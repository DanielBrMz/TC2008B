using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EnviromentManager : MonoBehaviour
{
    // Set this with a slider to set the delay in which in iteration is finished and we send the current enviroment info to the server
    [Header("Manager parameters")]
    [SerializeField] private float delay = 0.5f;
    public static float iterationDuration;

    private List<int> agentIds = new List<int>();

    public delegate void AgentActionDelegate(int Id, string action);
    public static event AgentActionDelegate OnAgentAction;

    private void Awake()
    {
        iterationDuration = delay;
    }

    public void Initialize(int agents)
    {
        for (int i = 0; i < agents; i++)
        {
            agentIds.Add(i);
        }

        StartCoroutine(RandomMovementCoroutine());
    }

    private IEnumerator RandomMovementCoroutine()
    {
        while (true)
        {
            yield return new WaitForSeconds(iterationDuration);
            // OnAgentAction?.Invoke(0, "MR");
            foreach (int agentId in agentIds)
            {
                char randomDirection = Utils.Direction2Name(Utils.directions[Random.Range(0, Utils.directions.Length)]);
                string instruction = $"M{randomDirection}";
                OnAgentAction?.Invoke(agentId, instruction);
            }
        }
    }
}

