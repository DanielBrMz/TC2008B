using UnityEngine;

public class Agent : MonoBehaviour
{
    [Header("Sensor values")]
    [SerializeField] private Vector3 sensorOffset = new Vector3(0f, 0.5f, 0f); // Offset from the agent's center
    [SerializeField] private float sensorDistance = 1f;
    [SerializeField] private float sensorVerticalOffset = 0.5f;
    [SerializeField] private float sensorSize = 1f;
    [SerializeField] private Material sensorMaterial; 
    

    // This are unique to the agent
    private Vector2 pos;
    private readonly Transform orientation; // this will probably go unused unless we implement animations or models
    

    // Sensor generation
    private GameObject sensorsContainer; // Wrapper for the colliders
    private GameObject[] sensors;
    private int[] sensorValues; // 0: nothing, 1: another agent, 2: object

    public static bool showColliders = false;

    private readonly Vector3[] directions = new Vector3[]
    {
        Vector3.forward,
        Vector3.back,
        Vector3.left,
        Vector3.right
    };

    // This setups to what the colliders will be able to collide with
    private void SetupCollisionMatrix()
    {
        // Sensors only interact with Agents, Objects, and Obstacles
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensor"), LayerMask.NameToLayer("Sensor"), true);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensor"), LayerMask.NameToLayer("Agent"), false);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensor"), LayerMask.NameToLayer("Object"), false);
        Physics.IgnoreLayerCollision(LayerMask.NameToLayer("Sensor"), LayerMask.NameToLayer("Obstacle"), false);
    }

    private void Awake()
    {
        SetupCollisionMatrix();
        GenerateSensors();
    }

    // Update is called once per frame
    void Update()
    {
        UpdateSensorPositions();
        UpdateColliderVisibility();
    }

    // This function can be hijacked to send the data tot he server
    public void UpdateSensorValue(int sensorIndex, int value)
    {
        sensorValues[sensorIndex] = value;
    }

    private void GenerateSensors()
    {
        // Create the sensors container
        sensorsContainer = new GameObject("SensorsContainer");
        sensorsContainer.transform.SetParent(transform);
        sensorsContainer.transform.localPosition = Vector3.zero;

        sensors = new GameObject[directions.Length];
        sensorValues = new int[directions.Length];

        for (int i = 0; i < directions.Length; i++)
        {
            string directionName = GetDirectionName(directions[i]);
            sensors[i] = GenerateSensor($"Sens{directionName}", directions[i]);
            sensors[i].transform.SetParent(sensorsContainer.transform);
            sensorValues[i] = 0;
        }
    }

    private GameObject GenerateSensor(string name, Vector3 direction)
    {
        GameObject sensor = new GameObject(name);
        sensor.transform.SetParent(transform); // Set the subject of this script as the parent
        sensor.layer = LayerMask.NameToLayer("Sensor");
        
        SphereCollider collider = sensor.AddComponent<SphereCollider>();
        collider.isTrigger = true;
        collider.radius = sensorSize / 2;
        collider.center = direction * sensorDistance + sensorOffset;

        SensorTrigger trigger = sensor.AddComponent<SensorTrigger>();
        trigger.parentAgent = this;
        trigger.sensorIndex = System.Array.IndexOf(directions, direction);

        // Crate visualizer
        GameObject visualizer = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        visualizer.transform.SetParent(sensor.transform);
        visualizer.transform.localPosition = collider.center;
        visualizer.transform.localScale = Vector3.one * (sensorSize / 2 * 2);
        Destroy(visualizer.GetComponent<SphereCollider>()); // Remove colliders since they are not needed
        visualizer.transform.GetComponent<Renderer>().material = sensorMaterial;
        visualizer.SetActive(showColliders);

        return sensor;
    }

    private void UpdateSensorPositions()
    {
        for (int i = 0; i < sensors.Length; i++)
        {
            sensors[i].transform.position = transform.position;
            // sensors[i].transform.rotation = transform.rotation;
        }
    }


    private void UpdateColliderVisibility()
    {
        foreach (GameObject sensor in sensors)
        {
            sensor.transform.GetChild(0).gameObject.SetActive(showColliders);
        }
    }

    public static void ToggleColliderVisibility()
    {
        showColliders = !showColliders;
    }

    private string GetDirectionName(Vector3 direction)
    {
        if (direction == Vector3.forward) return "F";
        if (direction == Vector3.back) return "B";
        if (direction == Vector3.left) return "L";
        if (direction == Vector3.right) return "R";
        return ""; // Default case, should not happen with your current directions array
    }
}
