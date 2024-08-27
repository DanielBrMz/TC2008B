using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Object : MonoBehaviour
{   
    [Header("Parameters")]
    public float size = 2f;

    [Header("Prefabs")]
    [SerializeField] private GameObject[] models;

    private static bool itemsVisible = false;


    private void Awake()
    {
        SetRandomModel();
        transform.localScale = Vector3.one * size;
    }

    private void Update() {
        UpdateObjectColliderVisibility();
    }

    private void UpdateObjectColliderVisibility()
    {
        transform.GetComponent<Renderer>().enabled = itemsVisible;
    }

    public static void ToggleItemColliderVisibility()
    {
        itemsVisible = !itemsVisible;
    }

    public void SetRandomModel()
    {
        if (models.Length > 0)
        {
            int randomIndex = Random.Range(0, models.Length);
            GameObject selectedModel = Instantiate(models[randomIndex], transform);
            selectedModel.transform.localPosition = Vector3.zero;
            selectedModel.layer = LayerMask.NameToLayer("Objects");
        }
    }
}